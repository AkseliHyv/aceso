from screens import Screen
from config import *
from machine import ADC
from piotimer import Piotimer
from helpers import file
from led import Led
import time

class MeasureScreen(Screen):
    def __init__(self, oled, navigate, sensor_fifo, history, profile, wlan, mqtt):
        super().__init__(oled, navigate)
        self.profile = profile
        self.history = history
        self.wlan = wlan
        self.mqtt = mqtt
        self.adc = ADC(ADC_PIN)
        self.led = Led(22)
        self.sensor_fifo = sensor_fifo
        self.tmr = None
        self.kubios = False
        self.measure_in_progress = False
        self.calibration_done = False
        self.measurement_dome = False
        self.sample_max = None
        self.sample_min = None
        self.sample_threshold = None
        self.average_buffer = []
        self.xloc = 0
        self.prev_y = None
        self.draw_index = 0 # draw happens 25 times a second, meaning that we can get elapsed time from keeping track of how many
                            # draws we have done
        self.current_peak_max = {
            "ms": 0,
            "val": 0
        }
        self.last_peak = None
        self.ppi = []
    
    def show(self, kubios):
        self.calibration_done = False
        self.kubios = kubios
        self.xloc = 0
        self.draw_index = 0
        self.ppi = []
        self._draw()
    
    def handle(self, event):
        if event == CANCEL_EVENT: # Cancel measurement
            if self.measure_in_progress:
                self._stop_measuring() 
            self.navigate(HOME_SCREEN)
        elif event == SELECT_EVENT and not self.calibration_done and not self.measure_in_progress: # Begin measuring
            # Prevent beginning measurement when offline and trying to use kubios
            if self.kubios and not self.wlan.isconnected():
                return
            self.measure_in_progress = True
            self.tmr = Piotimer(freq=250, mode=Piotimer.PERIODIC, callback=self._timer_handler)
        # If select pressed and over 30 secs have passed, end measurement early
        elif event == SELECT_EVENT and self.measure_in_progress and self.draw_index // 25 > 30: 
            self._stop_measuring()
            self._finish_measurement()
        elif event == SELECT_EVENT and self.calibration_done and not self.measure_in_progress: # Selecting after measurement brings main menu
            self.navigate(HOME_SCREEN)
    
    def handle_measurement(self):
        value = self.sensor_fifo.get()
        self.average_buffer.append(value)
        
        if self.xloc == 0: # Update sample values each full loop
            self.sample_max = max(self.sensor_fifo.data)
            self.sample_min = min(self.sensor_fifo.data)
            self.sample_threshold = int(self.sample_min + (self.sample_max - self.sample_min) / THRESHOLD_DIVIDER)
    
        if len(self.average_buffer) >= 10: # Combine 10 values into one to limit screen refreshes
            avg = sum(self.average_buffer) / 10
        
            # Calculate the y position on screen, showing flatline when calibrating or when flatlining
            # Also start calculating ppi only after calibration
            if self.calibration_done and self.sample_min != self.sample_max:
                self._calc_ppi(avg)
                ypos = 54 - int(max(0, min(54, (avg - self.sample_min) / (self.sample_max - self.sample_min) * 54)))
            else:
                ypos = 32
                if not self.calibration_done:
                    self._center_text("CALIBRATING", 20)
                    
            self._draw(ypos)
            self.average_buffer = []
        
        if self.draw_index // 25 > 60:
            self._stop_measuring()
            self._finish_measurement()

    def _calc_ppi(self, value):
        # If we go over threshold
        if value > self.sample_threshold:
            self.led.on()
            # While we are rising on the peak
            if value > self.current_peak_max["val"]:
                self.current_peak_max["val"] = value # Update peak value and timestamp
                self.current_peak_max["ms"] = time.time_ns()
        elif self.current_peak_max["val"] != 0: # We just left peak (current_peak_max["val"] is set to 0 at the end of this section of code)
            self.led.off()
            if self.last_peak == None: # If first peak in current measurement, skip PPI analysis
                self.last_peak = self.current_peak_max["ms"]
            else: # Subsequent peaks have PPI measured
                current_ppi = (self.current_peak_max["ms"] - self.last_peak) // 1000000
                if current_ppi > MIN_PPI and current_ppi < MAX_PPI:
                    self.ppi.append(current_ppi)
                self.last_peak = self.current_peak_max["ms"]
            self.current_peak_max["val"] = 0
                
    def _draw(self, ypos=None):
        if self.measure_in_progress is False: # Initial screen
            if self.kubios:
                self._draw_kubios_intro()
            else:
                self._draw_local_intro()
        elif self.measure_in_progress:
            self._draw_active_measurement(ypos)
        
        self.oled.show()
    
    def _draw_local_intro(self):
        self.oled.fill(0)
        self.oled.text("Press rotary", 0, 0, 1)
        self.oled.text("down to begin.", 0, 8, 1)
        self.oled.text("Analysis can", 0, 16, 1)
        self.oled.text("be ended after", 0, 24, 1)
        self.oled.text("30 seconds.", 0, 32, 1)
        self._back_hint()
        
    def _draw_kubios_intro(self):
        self.oled.fill(0)
        if self.wlan.isconnected() and self.mqtt["connected"]:
            self._draw_local_intro()
        else:
            self.oled.text("Kubios calc.", 0, 0, 1)
            self.oled.text("requires the", 0, 8, 1)
            self.oled.text("device to be", 0, 16, 1)
            self.oled.text("in online mode", 0, 24, 1)
            self.oled.text("and have mqtt", 0, 32, 1)
            self.oled.text("connection.", 0, 40, 1)
            self._back_hint()
    
    def _draw_active_measurement(self, ypos):
        if self.xloc == 0: # Clear screen when starting new loop
            self.oled.fill(0)
            self.prev_y = None

        if self.prev_y is not None: # Draw position changes as lines
            self.oled.line(self.xloc-1, self.prev_y, self.xloc, ypos, 1)
        else: # Draw single pixel instead when beginning new loop
            self.oled.pixel(self.xloc, ypos, 1)
        
        # Display timer and heartrate
        self.oled.fill_rect(0, 55, 128, 64, 1)
        self._left_text("T:" + str(60 - self.draw_index // 25), 56, 0)
        if len(self.ppi) > 0:
            mean_ppi = sum(self.ppi) // len(self.ppi)
            self._right_text("HR:" + str(60000 // mean_ppi), 56, 0)
        else:
            self._right_text("HR:  ", 56, 0)
        
        # Wait for one screen pass before we start displaying values
        if self.xloc == 127:
            self.calibration_done = True
        
        self.prev_y = ypos
        self.xloc = (self.xloc + 1) % 128
        self.draw_index += 1
        
    def _finish_measurement(self):
        self.oled.fill(0)
        
        # Check if we got enough values for measurement
        if len(self.ppi) < NEEDED_SAMPLES:
            self._center_text("NOT ENOUGH", 24)
            self._center_text("SAMPLES", 32)
        else:
            self.history["current_ppi"] = self.ppi
            file.save_file("./history.json", self.history)
            
            if self.kubios: # Go straight to analysis on kubios
                self.navigate(ANALYSIS_SCREEN, True)
            else:
                self._center_text("MEASUREMENT", 24)
                self._center_text("COMPLETE", 32)
            
        self._back_hint()
        self.oled.show()
                 
    def _timer_handler(self, tid):
        self.sensor_fifo.put(self.adc.read_u16())
    
    def _stop_measuring(self):
        if self.tmr:
            self.tmr.deinit()
        self.tmr = None
        self.measure_in_progress = False
        self.led.off()
