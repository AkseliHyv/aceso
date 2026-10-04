from screens import Screen
from config import *
from helpers.menu import Menu, ReadonlyOption

class HomeScreen(Screen):
    def __init__(self, oled, navigate, wlan, mqtt):
        super().__init__(oled, navigate)
        self.wlan = wlan
        self.mqtt = mqtt
        
        # Create list of main menu options
        options = [
            ReadonlyOption(label="Measure HR", value=None, callback=lambda: self.navigate(MEASURE_SCREEN, False)), # False means no kubios
            ReadonlyOption(label="HRV Analysis", value=None, callback=lambda: self.navigate(ANALYSIS_SCREEN, False)),
            ReadonlyOption(label="History", value=None, callback=lambda: self.navigate(HISTORY_SCREEN)),
            ReadonlyOption(label="KUBIOS", value=None, callback=lambda: self.navigate(MEASURE_SCREEN, True)), # True means using kubios
            ReadonlyOption(label="Patients", value=None, callback=lambda: self.navigate(PATIENTS_SCREEN))
        ]
        
        # Create menu from options
        self.menu = Menu(
            title = None,
            options = options,
            visible_count = 5,
            y_start = 0
        )
    
    def handle(self, event):
        self.menu.handle(event)
        if event != SELECT_EVENT:
            self._draw()
    
    def _draw(self):
        self.oled.fill(0)
        self.menu.draw(self.oled)
        self.oled.fill_rect(0, 55, 128, 64, 1)
        if not self.wlan.isconnected(): # Display OFFLINE if offline
            self._center_text("OFFLINE", 56, 0)
        elif not self.mqtt["connected"]: # Displkay NO MQTT if failed to connect to mqtt
            self._center_text("NO MQTT", 56, 0)
        else:
            self._center_text("ACESO", 56, 0)
        self.oled.show()
