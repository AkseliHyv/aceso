from screens import Screen
from config import *
from helpers.menu import Menu, ReadonlyOption, ButtonOption

class MeasurementScreen(Screen):
    """
    Scrollable list of measurement values.
    """
    def __init__(self, oled, navigate):
        super().__init__(oled, navigate)
        self.menu = None
    
    # Update options and menu each time we open measurement screen as the displayed data changes with payload
    def show(self, measurement):
        options = [
            ReadonlyOption(label=f"{measurement['name']}", value=None),
            ReadonlyOption(label="Mean HR", value=measurement["mean_hr"]),
            ReadonlyOption(label="Mean PPI", value=measurement["mean_ppi"]),
            ReadonlyOption(label="RMSSD", value=measurement["rmssd"]),
            ReadonlyOption(label="SDNN", value=measurement["sdnn"]),
            ReadonlyOption(label="SNS", value=measurement["sns"]),
            ReadonlyOption(label="PNS", value=measurement["pns"]),
            ReadonlyOption(label="STRESS", value=measurement["stress"]),
        ]
        self.menu = Menu(
            title=measurement["date"],
            options=options,
            visible_count=3,
        )
    
        self._draw()
        
    def handle(self, event):
        if event == CANCEL_EVENT:
            self.navigate(HOME_SCREEN)
        else:
            action = self.menu.handle(event)
            self._draw()

    def _draw(self):
        self.oled.fill(0)
        self.menu.draw(self.oled) # Call menu's own draw method
        self._back_hint()
        self.oled.show()