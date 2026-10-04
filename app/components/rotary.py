from machine import Pin
from config import *

class RotaryEncoder:
    def __init__(self, pin_a, pin_b, fifo):
        self.pin_a = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        self.pin_b = Pin(pin_b, Pin.IN, Pin.PULL_UP)
        self.fifo = fifo
        self.pin_a.irq(handler=self._handler, trigger=Pin.IRQ_RISING, hard=True)

    def _handler(self, pin):
        if self.pin_b():
            self.fifo.put(ROTARY_CCW_EVENT)
        else:
            self.fifo.put(ROTARY_CW_EVENT)
