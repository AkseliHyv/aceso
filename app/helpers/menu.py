from config import *
from helpers.icons import draw_arrow, draw_circle

class MenuOption:
    def __init__(self, label, value=None):
        self.label = label
        self.value = value
        self.is_editable = False

    def adjust(self, direction: int):
        pass

    def display_value(self) -> str:
        """String shown on-screen next to the label."""
        return "" if self.value is None else str(self.value)


class ReadonlyOption(MenuOption):
    """A label/value pair that cannot be changed via the rotary encoder."""
    def __init__(self, label, value, callback=None):
        super().__init__(label, value)
        self.callback = callback

class ButtonOption(MenuOption):
    """Same as ReadonlyOption, but different icon."""
    def __init__(self, label, callback=None):
        super().__init__(label, value=None)
        self.callback = callback


class NumericOption(MenuOption):
    """
    Integer value clamped between min_val and max_val.
    Each rotary turn increments/decrements by step.
    """
    def __init__(self, label, value: int, min_val: int, max_val: int, callback, step: int = 1):
        super().__init__(label, value)
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.callback = callback
        self.is_editable = True

    def adjust(self, direction: int):
        self.value = max(self.min_val, min(self.max_val, self.value + direction * self.step))
        self.callback(self.value)


class CycleOption(MenuOption):
    """
    Cycles through a fixed tuple/list of choices.
    """
    def __init__(self, label, value, choices, callback=None):
        super().__init__(label, value)
        self.choices = choices
        self.callback = callback
        self.is_editable = True

    def adjust(self, direction: int):
        idx = self.choices.index(self.value)
        self.value = self.choices[(idx + direction) % len(self.choices)]
        self.callback(self.value)

class Menu:
    """
    Scrollable vertical menu backed by a list of MenuOption objects.

    options: list of MenuOption
    title: optional header text drawn at y=2
    y_start: y pixel where the first visible row begins (default 14)
    row_height: pixels per row (default 10)
    visible_count: how many rows fit on screen at once (default: all options)
                   When set, a scroll window follows the cursor and up/down
                   arrows are drawn on the right edge to indicate hidden rows.
    """

    def __init__(self, options, title=None, y_start=18, row_height=10, visible_count=None):
        self.options = options
        self.title = title
        self.y_start = y_start
        self.row_height = row_height
        self.visible_count = visible_count if visible_count is not None else len(options)

        self.index = 0
        self.editing = False
        self._scroll_top = 0 # index of the first visible row

    def current(self):
        return self.options[self.index]

    def handle(self, event):
        if self.editing:
            self._handle_editing(event)
        else:
            self._handle_navigating(event)

    def draw(self, oled):
        """Render the menu (does NOT call oled.fill or oled.show)."""
        if self.title:
            oled.text(self.title, 2, 2, 1)

        self._update_scroll()
        visible = self.options[self._scroll_top : self._scroll_top + self.visible_count]

        for slot, opt in enumerate(visible):
            abs_index = self._scroll_top + slot
            y = self.y_start + slot * self.row_height
 
            if abs_index == self.index:
                direction = 'left' if self.editing else 'right'
                if isinstance(opt, ButtonOption):
                    draw_circle(oled, x=2, y=y + 4)
                else:
                    draw_arrow(oled, x=2, y=y + 4, direction=direction)
            
            val = opt.display_value()
            line = f"{opt.label}: {val}" if val else opt.label

            oled.text(line, 6, y, 1)
        
        self._draw_scroll_arrows(oled)

    def _update_scroll(self):
        """Keep the viewport window centred on the cursor."""
        # Scroll down if cursor moved below the window
        if self.index >= self._scroll_top + self.visible_count:
            self._scroll_top = self.index - self.visible_count + 1
        # Scroll up if cursor moved above the window
        if self.index < self._scroll_top:
            self._scroll_top = self.index

    def _draw_scroll_arrows(self, oled):
        """Draw up/down arrows when rows are hidden."""
        cx = OLED_WIDTH // 2 # Middle of the screen horizontally
        if self._scroll_top > 0:
            draw_arrow(oled, cx-1, self.y_start - 6, 'up')
        if self._scroll_top + self.visible_count < len(self.options):
            bottom_y = self.y_start + self.visible_count * self.row_height + 6
            draw_arrow(oled, cx-1, bottom_y, 'down')

    def _handle_editing(self, event):
        if event == ROTARY_CW_EVENT:
            self.current().adjust(+1)
        elif event == ROTARY_CCW_EVENT:
            self.current().adjust(-1)
        elif event in (SELECT_EVENT, CANCEL_EVENT):
            self.editing = False

    def _handle_navigating(self, event):
        n = len(self.options)
        if n == 0:
            return
        if event == ROTARY_CW_EVENT:
            self.index = (self.index + 1) % n
        elif event == ROTARY_CCW_EVENT:
            self.index = (self.index - 1) % n
        elif event == SELECT_EVENT:
            opt = self.current()
            if isinstance(opt, ReadonlyOption) or isinstance(opt, ButtonOption):
                if opt.callback:
                    opt.callback()
            elif opt.is_editable:
                self.editing = True
