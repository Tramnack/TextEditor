from typing import List, Tuple, Optional

UNSUPPORTED_CHARS = ["\a", "\b", "\f", "\r", "\v"]


class UnsupportedCharacterError(Exception):
    """Exception raised when an unsupported character is encountered."""

    def __init__(self, char: str):
        self.message = f"Unsupported character: {char}"
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"


class TextEditor:
    def __init__(self, line_limit: int, text: Optional[str] = None, ):

        self.__validate_line_limit(line_limit)

        self._logic_lines = None
        self._display_lines = None

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
        for i, l in enumerate(self._display_lines):
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

        line = min(line, len(self._logic_lines))
        if line >= len(self._logic_lines):
            line = len(self._logic_lines) - 1
            char = len(self._logic_lines[line])
        else:
            char = min(char, len(self._logic_lines[line]))
        # print(line, char)
        self._abs_cursor = min(self._wrapped_to_absolute_index(line, char), len(self._text))
        # print(self._abs_cursor)

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
        self._display_lines = lines

        self._logic_lines = [
            c
            for sub_line in self._display_lines
            for c in sub_line
        ]

    def get_lines(self) -> List[str]:
        return self._logic_lines

    def get_sub_lines(self) -> List[List[str]]:
        return self._display_lines

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
        self.cursor = len(self._logic_lines) - 1, len(self._logic_lines[-1])

    # Text Manipulation
    def insert(self, text: str):
        if not isinstance(text, str):
            raise TypeError("text must be of type str")
        elif len(text) == 0:
            return
        elif any(c in text for c in UNSUPPORTED_CHARS):
            for c in UNSUPPORTED_CHARS:
                if c in text:
                    raise UnsupportedCharacterError(c)
        else:
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

        for orig_display_lines in self._display_lines:
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

    def _absolute_to_wrapped_index_new(self, abs_index: int) -> tuple[int, int]:
        """
        Convert an absolute index in the original text into a wrapped (line, col).

        Returns (wrapped_line_index, col) where:
          - wrapped_line_index is the zero-based index counting *wrapped sub-lines*
            across the whole document (first sub-line of first original line is 0).
          - col is the column inside that wrapped sub-line. It may equal len(subline)
            in the case the absolute index points to the newline immediately after a
            subline that is the last subline of its original line.
        Assumptions:
          - self._wrapped_sub_lines is a list of original lines; each original line
            is a list of its wrapped sub-lines (strings).
          - There is a single newline character between original lines (length 1).
          - We clamp abs_index to [0, len(self._text)] if self._text exists.
        """
        # clamp to valid range if we have the original text
        abs_index = max(0, min(abs_index, len(self._text)))

        wrapped_index = 0  # counts wrapped sub-lines across the whole doc
        running_abs = 0  # absolute index while we walk sub-lines

        for orig_line in self._display_lines:
            num_sub = len(orig_line)
            for i, sub in enumerate(orig_line):
                start = running_abs
                end = start + len(sub)  # exclusive end for the subline content

                # Case 1: index falls strictly inside this subline content
                if abs_index < end:
                    return wrapped_index, abs_index - start

                # Case 2: index equals end (right after this subline)
                if abs_index == end:
                    # If this subline is the last subline of the original line,
                    # this position is the newline char — map it to this wrapped line
                    if i == num_sub - 1:
                        return wrapped_index, len(sub)
                    # Otherwise, it's the start of the next subline (same original line).
                    # We'll continue the loop and match the next subline (which has start==end).

                # advance running_abs past this subline
                running_abs = end
                # If this was the last subline in its original line, account for newline char
                if i == num_sub - 1:
                    running_abs += 1

                wrapped_index += 1

        # If we get here, abs_index is beyond all characters (e.g., equal to len(text))
        # Map to the last wrapped sub-line, at its end.
        if wrapped_index == 0:
            # no sub-lines at all (empty doc)
            return 0, 0

        # wrapped_index is now count of all sub-lines; last subline index is wrapped_index - 1
        last_wrapped = wrapped_index - 1
        # find the last subline length to set column correctly
        # walk to last subline to fetch its length (cheap in practice)
        for orig_line in self._display_lines[::-1]:
            if orig_line:
                last_sub = orig_line[-1]
                return last_wrapped, len(last_sub)

        # fallback (shouldn't happen)
        return last_wrapped, 0

    def _absolute_to_wrapped_index(self, abs_index: int) -> Tuple[int, int]:
        """
        Convert an absolute index in the original text string
        into a wrapped (line, col) cursor position.
        """

        abs_index = max(0, min(abs_index, len(self._text)))

        wrapped_line = 0
        for logic_line in self._display_lines:
            for i, display_line in enumerate(logic_line):
                if abs_index <= len(display_line):
                    # allow cursor to sit "on" newline if last display line
                    if i == len(logic_line) - 1:
                        return wrapped_line, abs_index
                    line_offset, char_index = divmod(abs_index, self._line_limit)
                    return wrapped_line + line_offset, char_index
                else:
                    abs_index -= len(display_line)
                wrapped_line += 1
            # consume the newline between original lines
            abs_index -= 1

        # fall back: clamp to last wrapped subline, end of line
        return wrapped_line - 1, len(self._display_lines[-1][-1])
