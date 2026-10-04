from screens import Screen
from config import *
from math import sqrt
from helpers import file, mqtt
import time
from helpers.mqtt import publish_and_wait
import json

class AnalysisScreen(Screen):
    def __init__(self, oled, navigate, fifo, history, profile, wlan, mqtt):
        super().__init__(oled, navigate)
        self.fifo = fifo
        self.history = history
        self.profile = profile
        self.wlan = wlan
        self.mqtt = mqtt
        self.using_kubios = False
    
    def show(self, using_kubios):
        #Called each time this screen opens. Gets mode (local/kubios) from payload and
        #passes it to other parts to manage two different functionalities in one class
        self.using_kubios = using_kubios
        # Check if we have enough data for analysis
        has_data = len(self.history["current_ppi"]) >= NEEDED_SAMPLES
        self._draw(has_data)
        if has_data:
            try:
                self._hrv_analysis()
            except Exception as e:
                print(e)
                self.oled.fill(0)
                self._center_text("ERROR DURING", 24)
                self._center_text("ANALYSIS", 32)
                self._back_hint()
                self.oled.show()
        
    def handle(self, event):
        if event == CANCEL_EVENT:
            self.navigate(HOME_SCREEN)
        
    def _draw(self, has_data):
        self.oled.fill(0)
        self._back_hint()
        
        if has_data:
            if self.using_kubios: # Kubios analysis screen
                self._center_text("ANALYZING W/", 24)
                self._center_text("KUBIOS", 32)
            else: # Local analysis screen
                self._center_text("ANALYZING...")
        else: # Not enough data screen
            self._center_text("NO DATA", 24)
            self._center_text("TO ANALYZE", 32)
            
        self.oled.show()
    
    def _hrv_analysis(self):
        ppi_list = self.history["current_ppi"]
        
        # Calculate data via kubios or locally depending on choice
        kubios_calc = mean_hr = rmssd = sdnn = None
        mean_ppi = sum(ppi_list) // len(ppi_list)
        if self.using_kubios: # This is only possible if online and mqtt connection is successful
            kubios_calc = self._calc_with_kubios(ppi_list)
        else:
            mean_hr = 60000 // mean_ppi
            rmssd = self._calc_rmssd(ppi_list)
            sdnn = self._calc_sdnn(ppi_list)
        
        # Store meausurements in a set
        measurements = {
            "patient_id": self.profile["ID"],
            "mean_hr": kubios_calc["mean_hr_bpm"] if kubios_calc is not None else mean_hr,
            "mean_ppi": mean_ppi,
            "rmssd": kubios_calc["rmssd_ms"] if kubios_calc is not None else rmssd,
            "sdnn": kubios_calc["sdnn_ms"] if kubios_calc is not None else sdnn,
            "sns": kubios_calc["sns_index"] if kubios_calc is not None else None,
            "pns": kubios_calc["pns_index"] if kubios_calc is not None else None,
        }
            
        if self.wlan.isconnected():
            # Get local timestamp
            t = time.localtime(time.time() + TIME_OFFSET)
            date = f"{str(t[0])[-2:]}.{t[1]:02d}.{t[2]:02d} {t[3]:02d}:{t[4]:02d}"
            
            # Save to database (using non-local time for remote storing)
            if self.mqtt["connected"]:
                self._save_to_database({"mac": self.mqtt["mac"], "timestamp": time.time()} | measurements)
        else:
            date = f"offl. - {self.profile["Name"]}"
        
        # Create full measurement from analyzed data to save into local history
        # Stress is added at this point as it is not supposed to be added to database
        full_measurement = {"date": date, "name": self.profile["Name"]} | measurements | {
            "stress": kubios_calc["stress_index"] if kubios_calc is not None else None
        }
        
        self.history["history"].append(full_measurement)
        self.history["current_ppi"] = []
        file.save_file("./history.json", self.history)
        
        self.navigate(MEASUREMENT_SCREEN, full_measurement)
    
    def _calc_rmssd(self, ppi_list):
        diff_sq_sum = 0
        for i in range(len(ppi_list) - 1):
            diff = ppi_list[i+1] - ppi_list[i]
            diff_sq_sum += diff ** 2
        return round(sqrt(diff_sq_sum / (len(ppi_list) - 1)), 2)

    def _calc_sdnn(self, ppi_list):
        avg_ppi = sum(ppi_list) / len(ppi_list)
        sum_sq_dist = sum((x - avg_ppi) ** 2 for x in ppi_list)
        return round(sqrt(sum_sq_dist / (len(ppi_list) - 1)), 2)
    
    def _calc_with_kubios(self, ppi_list):
        # Returns kubios analysis as a dictionary
        self.mqtt["client"].set_callback(self._listen_for_response)
        self.mqtt["client"].subscribe("kubios/response")
        
        res = publish_and_wait(
            self.mqtt,
            b"kubios/request",
            {
                "mac": self.mqtt["mac"],
                "type": "RRI",
                "data": ppi_list,
                "analysis": { "type": "readiness" }
            }
        )["data"]["analysis"]
        
        kubios_data = {
            "mean_hr_bpm": round(res["mean_hr_bpm"], 2),
            "rmssd_ms": round(res["rmssd_ms"], 2),
            "sdnn_ms": round(res["sdnn_ms"], 2),
            "sns_index": round(res["sns_index"], 2),
            "pns_index": round(res["pns_index"], 2),
            "stress_index": round(res["stress_index"], 2)
        }
        return kubios_data
    
    def _save_to_database(self, data):
        self.mqtt["client"].publish("database/records/add", json.dumps(data))
    
    def _listen_for_response(self, topic, msg):
        self.mqtt["last_message"] = msg
