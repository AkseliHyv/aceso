import micropython
micropython.alloc_emergency_exception_buf(200)
from machine import Pin, ADC, I2C
from ssd1306 import SSD1306_I2C
from fifo import Fifo
from umqtt.simple import MQTTClient
from components import Button, RotaryEncoder
from screens import *
from config import *
from helpers.file import *
import ntptime
import network
import time
from helpers.mqtt import publish_and_wait

class Program:
    def __init__(self):
        # Setup components, fifo, persistent storage items and currently stored ppi value
        self.i2c  = I2C(1, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
        self.oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, self.i2c)
        self.fifo = Fifo(256)
        self.sensor_fifo = Fifo(500)
        self.wlan = network.WLAN(network.STA_IF)
        self.mqtt = {
            "client": None,
            "connected": False,
            "last_message": None,
            "mac": None
        }
        
        self.profile = {'ID': -1, 'DeviceID': -1, 'Name': 'Unknown'}
        self.patients = []
        self.history = load_file("./history.json")
        
        # Setup screens for program
        self.screens = {
            STARTUP_SCREEN: StartupScreen(self.oled, self.navigate, self.fifo),
            HOME_SCREEN: HomeScreen(self.oled, self.navigate, self.wlan, self.mqtt),
            MEASURE_SCREEN: MeasureScreen(self.oled, self.navigate, self.sensor_fifo, self.history, self.profile, self.wlan, self.mqtt),
            ANALYSIS_SCREEN: AnalysisScreen(self.oled, self.navigate, self.fifo, self.history, self.profile, self.wlan, self.mqtt),
            HISTORY_SCREEN: HistoryScreen(self.oled, self.navigate, self.history),
            PATIENTS_SCREEN: PatientsScreen(self.oled, self.navigate, self.profile, self.patients),
            MEASUREMENT_SCREEN: MeasurementScreen(self.oled, self.navigate)
        }
        
        self._active = None # No active screen on start

    def navigate(self, screen, payload=None):
        # Hide currently active screen
        if self._active is not None:
            self._active.hide()
        
        # Get the new screen object
        self._active = self.screens[screen]
                
        # Call screen object's show function to display it
        self._active.show(payload)
    
    def run(self):
        # Navigate to startup screen initially
        self.navigate(STARTUP_SCREEN)
                
        # Attempt connecting to internet, and if successful connecting to mqtt and syncing time
        self._connect_to_wlan()
        if self.wlan.isconnected():
            try:
                self._initialize_mqtt()
                self.mqtt["connected"] = True
            except:
                print("Failed to connect to mqtt")
            self._sync_ntp()
            
        # Register inputs
        Button(SELECT_PIN, SELECT_EVENT, self.fifo)
        Button(CANCEL_PIN, CANCEL_EVENT, self.fifo)
        RotaryEncoder(ROTA_PIN, ROTB_PIN, self.fifo)
            
        # Main application loop
        while True:
            if self.fifo.has_data(): # Get event from fifo and handle it in active screen object
                event = self.fifo.get()
                self._active.handle(event)
            if self.sensor_fifo.has_data(): # Call handle measurement as sensor data rolls in
                try:
                    # While sensor only puts data in when within measure screen, edge cases exist where
                    # the sensor might have data put in as said screen is left. try except handles this specific case
                    self._active.handle_measurement()
                except:
                    pass
                
    def _connect_to_wlan(self):
        self.wlan.active(True)
        if not self.wlan.isconnected():
            self.wlan.connect(SSID, PASSWORD)
            max_wait = 10
            while max_wait > 0:
                if self.wlan.status() < 0 or self.wlan.status() >= 3:
                    break            
                max_wait -= 1
                print("Connecting to Wi-Fi...")
                time.sleep(1)
        if self.wlan.isconnected():
            print("Connected.")
            return True
        else:
            print("Failed to connect.")
            return False
    
    def _initialize_mqtt(self):
        self.mqtt["mac"] = ubinascii.hexlify(network.WLAN().config('mac')).decode().upper()
        self.mqtt["client"] = MQTTClient(client_id = self.mqtt["mac"], server = BROKER_IP, port = BROKER_PORT)
        self.mqtt["client"].connect()
        self.mqtt["client"].set_callback(self._listen_for_response)
        self.mqtt["client"].subscribe("database/response")
        
        # Register device
        publish_and_wait(
            self.mqtt,
            b"database/devices/add",
            {"mac": self.mqtt["mac"], "device_name": DEVICE_NAME}
        )
        
        # Fetch and set patients
        self.patients = publish_and_wait(
            self.mqtt,
            b"database/patients/list",
            {"mac": self.mqtt["mac"]}
        )["data"]
        
        # Add placeholder users if empty
        if len(self.patients) == 0:
            for name in ["Akseli", "Miro", "Nikolai"]:
                publish_and_wait(
                    self.mqtt,
                    b"database/patients/add",
                    {"mac": self.mqtt["mac"], "patient_name": name}
                )
            self.patients = publish_and_wait(
                self.mqtt,
                b"database/patients/list",
                {"mac": self.mqtt["mac"]}
            )["data"]
        
        # Select first patient in the list initially
        self.profile["ID"] = self.patients[0]["ID"]
        self.profile["DeviceID"] = self.patients[0]["DeviceID"]
        self.profile["Name"] = self.patients[0]["Name"]
        
        self.screens[PATIENTS_SCREEN] = PatientsScreen(self.oled, self.navigate, self.profile, self.patients)

    # Update stored message when callback is called
    def _listen_for_response(self, topic, msg):
        self.mqtt["last_message"] = msg
    
    def _sync_ntp(self):
        try:
            # Try to get the current time from the internet
            ntptime.settime()
            print("Time synced:", time.localtime())
        except Exception as e:
            print("NTP sync failed:", e)


program = Program()
program.run()
