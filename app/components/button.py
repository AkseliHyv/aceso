from machine import Pin
import time

class Button:
    def __init__(self, pin, event_id, fifo):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.event_id = event_id
        self.fifo = fifo
        self.pin.irq(handler=self._handler, trigger=Pin.IRQ_RISING, hard=True)
        self._last_press = 0

    # Handler has debounce
    def _handler(self, pin):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_press) > 200:
            self.fifo.put(self.event_id)
            self._last_press = now
