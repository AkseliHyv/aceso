from screens import Screen
from config import *
from helpers.menu import Menu, ReadonlyOption
from helpers.file import *

class PatientsScreen(Screen):
    def __init__(self, oled, navigate, profile, patients):
        super().__init__(oled, navigate)
        self.profile = profile
        self.patients = patients
        self.menu_options = []
        self.menu = None
    
    def handle(self, event):
        if event == CANCEL_EVENT:
            self.navigate(HOME_SCREEN)
        elif len(self.patients) != 0 and event == SELECT_EVENT:
            self.profile["ID"] = self.patients[self.menu.index]["ID"]
            self.profile["DeviceID"] = self.patients[self.menu.index]["DeviceID"]
            self.profile["Name"] = self.patients[self.menu.index]["Name"]
            # Re-initialize menu
            self.menu_options = [ReadonlyOption(label=f"""{entry["ID"]}-{entry["Name"]}""", value="sel." if self.profile["ID"] == entry["ID"] else None) for entry in self.patients]
            self.menu = Menu(
                title="PATIENT",
                options=self.menu_options,
                visible_count=3
            )
            self._draw()
        elif len(self.patients) != 0: # Handle menu only when there are patients in the list
            self.menu.handle(event)
            self._draw()
            
    def show(self, payload):
        # Display patients if we successfully fetched them, otherwise show failure message
        if len(self.patients) == 0:
            self.menu_options = [
                ReadonlyOption(label="Could not", value=""),
                ReadonlyOption(label="fetch patients.", value="")
            ]
        else:
            self.menu_options = [ReadonlyOption(label=f"""{entry["ID"]}-{entry["Name"]}""", value="sel." if self.profile["Name"] == entry["Name"] else None) for entry in self.patients]
        
        self.menu = Menu(
            title="PATIENT",
            options=self.menu_options,
            visible_count=3
        )
        self._draw()

    def _draw(self):
        self.oled.fill(0)
        self.menu.draw(self.oled)
        self._back_hint()
        self.oled.show()
    
    def _update_settings(self, property, value):
        self.profile[property] = value
