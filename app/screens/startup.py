from screens import Screen
from helpers.icons import *
import time
from config import *

class StartupScreen(Screen):
    def __init__(self, oled, navigate, fifo):
        super().__init__(oled, navigate)
        self.fifo = fifo
        
    def handle(self, event):
        # Wait for specific MOVE_ON_EVENT to prevent all other events from causing navigation to happen
        if event == MOVE_ON_EVENT:
            self.navigate(HOME_SCREEN)

    def _draw(self):
        self.oled.fill(0)
        draw_splash(self.oled)
        self.oled.show()
        time.sleep(1.5)
                            
        self.fifo.put(MOVE_ON_EVENT) # Put move on event into fifo to proc handle method