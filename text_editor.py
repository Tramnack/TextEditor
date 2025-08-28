from typing import List, Tuple, Optional

class UnsupportedCharacterError(Exception):
    """Exception raised when an unsupported character is encountered."""

    def __init__(self, char: str):
        self.message = f"Unsupported character: {repr(char)}"
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"


class TextEditor:
    UNSUPPORTED_CHARS = ["\a", "\b", "\f", "\r", "\v"]

    def __init__(self, line_limit: int, text: Optional[str] = None, ):

        self.__validate_line_limit(line_limit)

        self._logic_lines: List[List[str]] = None
        self._display_lines: List[str] = None

        self._line_limit = line_limit
        self._text = ""

        self._abs_cursor = len(self._text)

        if not isinstance(text, str | None):
            raise TypeError("text must be of type str or None")
        elif text is not None:
            self.insert(text)

    # Cursor
    @staticmethod
    def __validate_cursor(pos):
        if not isinstance(pos, tuple | list):
            raise TypeError("pos must be of type tuple or list")
        elif len(pos) != 2:
            raise ValueError("pos must be of length 2")
        elif not all(isinstance(i, int) for i in pos) or any(isinstance(i, bool) for i in pos):
            raise TypeError("pos elements must be of type int")
        elif pos[0] < 0:
            raise ValueError("Line must be non-negative")
        elif pos[1] < 0:
            raise ValueError("Column must be non-negative")

    @property
    def line_cursor(self):
        line, char = self._absolute_to_wrapped_index(self._abs_cursor)

        total_lines = 0
        for i, l in enumerate(self._logic_lines):
            total_chars = 0
            for s, sub_line in enumerate(l):
                if total_lines == line:
                    return i, total_chars + char
                total_chars += len(sub_line)
                total_lines += 1

    @property
    def cursor(self) -> Tuple[int, int]:
        return self._absolute_to_wrapped_index(self._abs_cursor)

    @cursor.setter
    def cursor(self, pos: Tuple[int, int]):

        self.__validate_cursor(pos)

        line, char = pos
        if char > self._line_limit:
            char -= self._line_limit
            line += 1

        line = min(line, len(self._display_lines))
        if line >= len(self._display_lines):
            line = len(self._display_lines) - 1
            char = len(self._display_lines[line])
        else:
            char = min(char, len(self._display_lines[line]))
        self._abs_cursor = min(self._wrapped_to_absolute_index(line, char), len(self._text))

    # Text
    @property
    def text(self):
        return self._text

    @text.deleter
    def text(self):
        self._text = ""
        self._abs_cursor = 0

    @property
    def _text(self):
        return self.__text

    @_text.setter
    def _text(self, text):
        self.__text = text
        self._wrap_lines()

    # No text setter. How to handle cursor?

    def _wrap_lines(self):
        # TODO: Use textwrap wrap instead?
        #       Warning: Works differently than this implementation! (Not a 1:1 replacement.)
        lines = []
        for raw_line in self._text.split("\n"):
            sub_lines = []
            while len(raw_line) > self._line_limit:
                sub_lines.append(raw_line[:self._line_limit])
                raw_line = raw_line[self._line_limit:]
            sub_lines.append(raw_line)  # remainder (possibly empty string)
            lines.append(sub_lines)
        self._logic_lines = lines

        self._display_lines = [
            c
            for sub_line in self._logic_lines
            for c in sub_line
        ]

    def get_display_lines(self) -> List[str]:
        """Returns a list of display lines."""
        return self._display_lines

    def get_logic_lines(self) -> List[List[str]]:
        """Returns a list of logic lines. Each logic line is a list of display lines."""
        return self._logic_lines

    # Line limit
    @staticmethod
    def __validate_line_limit(line_limit):
        if not isinstance(line_limit, int) or isinstance(line_limit, bool):
            raise TypeError("line_limit must be of type int")
        elif line_limit <= 0:
            raise ValueError("line_limit must be greater than 0")

    @property
    def line_limit(self):
        return self._line_limit

    @line_limit.setter
    def line_limit(self, value):
        self.__validate_line_limit(value)

        if value == self._line_limit:
            return

        self._line_limit = value
        self._wrap_lines()

    # Movement
    def move_left(self):
        self._abs_cursor = max(self._abs_cursor - 1, 0)

    def move_right(self):
        self._abs_cursor = min(self._abs_cursor + 1, len(self._text))

    def move_up(self):
        line, char = self.cursor

        line -= 1

        if char == self._line_limit:
            char = 0
            line += 1
        if line < 0 or char < 0:
            line = 0
            char = 0
        self.cursor = line, char

    def move_down(self):
        line, char = self.cursor

        if char == self._line_limit:
            char = 0

        line += 1
        self.cursor = line, char

    def move_home(self):
        self.cursor = 0, 0

    def move_end(self):
        self.cursor = len(self._display_lines) - 1, len(self._display_lines[-1])

    # Text Manipulation
    def insert(self, text: str):
        if not isinstance(text, str):
            raise TypeError("text must be of type str")
        elif len(text) == 0:
            return

        for c in self.UNSUPPORTED_CHARS:
            if c in text:
                raise UnsupportedCharacterError(c)
        self._insert(text)

    def _insert(self, text: str):
        """Insert text at current cursor position"""
        self._text = self._text[:self._abs_cursor] + text + self._text[self._abs_cursor:]
        self._abs_cursor += len(text)

    def delete(self):
        if self._abs_cursor == len(self._text):
            return

        self._text = (self._text[:self._abs_cursor] +
                      self._text[self._abs_cursor + 1:])

    def backspace(self):
        if self._abs_cursor == 0:
            return
        self.move_left()
        self.delete()

    # Conversion

    def _wrapped_to_absolute_index(self, line: int, col: int) -> int:
        """
        Convert a wrapped (line, col) cursor into an absolute index in the original text.
        """
        if not self._text:
            return 0

        wrap_width = self._line_limit + 1

        # normalize column overflow into wrapped-line increments
        line += col // wrap_width
        col = col % wrap_width

        # fast path for the very first wrapped line
        if line == 0:
            return col

        abs_index = 0
        remaining_wrapped = line  # how many wrapped display-lines we still need to skip

        for orig_display_lines in self._logic_lines:
            count = len(orig_display_lines)

            if remaining_wrapped >= count:
                # consume all display-lines of this original line
                for sub in orig_display_lines:
                    abs_index += len(sub)
                remaining_wrapped -= count
                # after a full original line, account for the newline separator
                abs_index += 1
            else:
                # consume only the first `remaining_wrapped` sub-lines of this original line
                for sub in orig_display_lines[:remaining_wrapped]:
                    abs_index += len(sub)
                break

        # add the column offset inside the target wrapped line
        abs_index = min(abs_index + col, len(self._text))
        return abs_index

    def _absolute_to_wrapped_index(self, abs_index: int) -> Tuple[int, int]:
        """
        Convert an absolute index in the original text string
        into a wrapped (line, col) cursor position.
        """

        abs_index = max(0, min(abs_index, len(self._text)))

        wrapped_line = 0
        for logic_line in self._logic_lines:
            for i, display_line in enumerate(logic_line):
                if abs_index <= len(display_line):
                    # allow cursor to sit "on" newline if last display line
                    if i == len(logic_line) - 1:
                        return wrapped_line, abs_index
                    line_offset, char_index = divmod(abs_index, len(display_line))
                    return wrapped_line + line_offset, char_index
                else:
                    abs_index -= len(display_line)
                wrapped_line += 1
            # consume the newline between original lines
            abs_index -= 1

        # fall back: clamp to last wrapped subline, end of line
        return wrapped_line - 1, len(self._logic_lines[-1][-1])
