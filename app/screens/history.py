from screens import Screen
from config import *
from helpers.menu import Menu, ReadonlyOption

class HistoryScreen(Screen):
    def __init__(self, oled, navigate, history):
        super().__init__(oled, navigate)
        self.history = history
        self.menu = None
    
    def show(self, payload=None):
        # Update menu each time we enter the screen as history might have updated
        self.menu = Menu(
            title = "HISTORY",
            options = [ReadonlyOption(label=entry["date"], value=None) for entry in self.history["history"]],
            visible_count = 3
        )
        self._draw()
        
    def handle(self, event):
        if event == CANCEL_EVENT:
            self.navigate(HOME_SCREEN)
        elif event == SELECT_EVENT:
            self.navigate(MEASUREMENT_SCREEN, self.history["history"][self.menu.index])
        else:
            self.menu.handle(event)
            self._draw()
    
    def _draw(self):
        self.oled.fill(0)
        self.menu.draw(self.oled)
        self._back_hint()
        self.oled.show()