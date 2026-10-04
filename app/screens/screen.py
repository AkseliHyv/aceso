from config import *
from helpers.icons import draw_arrow

class Screen:
    def __init__(self, oled, navigate):
        self.oled = oled
        self.navigate = navigate
    
    def show(self, payload=None):
        self._draw()
    
    def hide(self):
        pass
    
    def handle(self, event, navigate):
        pass
    
    def _draw(self):
        pass

    def _center_text(self, text, y=28, color=1):
        x = OLED_HEIGHT - len(text) * 4
        self.oled.text(text, x, y, color)

    def _left_text(self, text, y=28, color=1):
        self.oled.text(text, 0, y, color)

    def _right_text(self, text, y=28, color=1):
        x = OLED_WIDTH - len(text) * 8
        self.oled.text(text, x, y, color)

    def _back_hint(self, color=1):
        draw_arrow(self.oled, x=1, y=OLED_HEIGHT-5, direction='left', color=color)
        self.oled.text("SW0", 8, OLED_HEIGHT-8, color)
    
    def _horizontal_navigation_hint(self):
        cy = OLED_HEIGHT // 2

        draw_arrow(self.oled, x=0, y=cy, direction='left')
        draw_arrow(self.oled, x=OLED_WIDTH - 1, y=cy, direction='right')
