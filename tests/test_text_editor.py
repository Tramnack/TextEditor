from abc import abstractmethod
from typing import Tuple, Optional

import pytest

from text_editor import TextEditor, UnsupportedCharacterError


def editor_factory(
        text: str = "",
        line_limit: int = 10,
        cursor: Optional[Tuple[int, int]] = None
) -> Tuple[TextEditor, str]:
    editor = TextEditor(line_limit, text)
    if cursor:
        editor.cursor = cursor

    return editor, editor.text


class AbstractTestMove:
    """Abstract base class for cursor movement tests."""

    @abstractmethod
    def test_move_in_empty_text(self):
        """Test the movement method when there is no text."""
        pass

    @abstractmethod
    def test_move_across_newline(self):
        """Test the movement method over a newline. (From one logic line to another)"""
        pass

    @abstractmethod
    def test_move_out_of_bounds(self):
        """Test the moving the cursor out of bounds. (Nothing should happen.)"""
        pass

    @abstractmethod
    def test_move_from_empty_line(self):
        """Cursor moves from an empty logic line."""
        pass

    @abstractmethod
    def test_move_to_empty_line(self):
        """Cursor moves to an empty logic line."""
        pass

    @abstractmethod
    def test_move_when_line_wraps_exact_boundary(self):
        """Special case: last line ends exactly at wrap boundary."""
        pass

    @abstractmethod
    def test_move_multi_logic_line_document(self):
        """Cursor moves across multiple logic lines correctly."""
        pass

    @abstractmethod
    def test_move_multi_display_line_document(self):
        """Cursor moves across multiple display lines correctly."""
        pass

    @abstractmethod
    def test_move_multi_line_document(self):
        """Cursor moves across multiple logic and display lines correctly."""
        pass


class AbstractTestHorizontalMove(AbstractTestMove):
    """Abstract base class for horizontal movement tests."""

    @abstractmethod
    def test_move_within_display_line(self):
        """Test the movement method when the cursor is within a display line."""
        pass

    @abstractmethod
    def test_multi_move_within_display_line(self):
        pass

    @abstractmethod
    def test_cursor_moves_across_wrapped_line(self):
        """Test the movement method over a wrapped line. (From one display line to another)"""
        pass


class AbstractTestVerticalMove(AbstractTestMove):
    """Abstract base class for vertical movement tests."""

    @abstractmethod
    def test_move_between_display_lines(self):
        """Test the movement method when the cursor is between display lines."""
        pass

    @abstractmethod
    def test_move_on_first_display_line(self):
        """Test the movement method when the cursor is on the first display line."""
        pass

    @abstractmethod
    def test_move_on_last_display_line(self):
        """Test the movement method when the cursor is on the first display line."""
        pass


class TestInitTextEditor:
    def test_init_defaults(self):
        """Default initialization should produce an empty editor with cursor at start."""
        editor = TextEditor(line_limit=10, text=None)

        # Empty text state
        assert editor.text == ""
        assert editor.get_lines() == [""]

        # Cursor should start at beginning
        assert editor.cursor == (0, 0)
        assert editor.line_cursor == (0, 0)

        # Sub-lines should also be empty
        assert editor.get_sub_lines() == [[""]]

    class TestLineLimit:
        """Test validation and behavior of the line_limit parameter."""

        @pytest.mark.parametrize("line_limit", [1, 2, int(1e10)])
        def test_line_limit_accepts_positive_integers(self, line_limit):
            """line_limit must accept positive integers."""
            editor = TextEditor(line_limit=line_limit)
            # Should preserve the exact int value
            assert editor.line_limit == int(line_limit)

        @pytest.mark.parametrize("line_limit", [-100, -1, 0])
        def test_line_limit_rejects_non_positive_integers(self, line_limit):
            """line_limit <= 0 should raise ValueError."""
            with pytest.raises(ValueError,
                               match="must be greater than 0"):
                TextEditor(line_limit=line_limit)

        @pytest.mark.parametrize("line_limit", ["a", None, 2.0, [], {}, float("inf"), float("nan")])
        def test_line_limit_rejects_invalid_types(self, line_limit):
            """Non-int types should raise TypeError."""
            with pytest.raises(TypeError,
                               match="must be of type int"):
                TextEditor(line_limit=line_limit)

        def test_line_limit_bool_is_rejected(self):
            """Booleans are ints in Python, but should not be accepted as line_limit."""
            with pytest.raises(TypeError,
                               match="must be of type int"):
                TextEditor(line_limit=True)

    class TestText:
        """Test the text parameter"""

        @pytest.mark.parametrize("text", [None, ""])
        def test_empty_text(self, text):
            """None or empty string should initialize as empty."""
            editor = TextEditor(line_limit=10, text=text)
            assert editor.text == ""
            assert editor.get_lines() == [""]
            assert editor.get_sub_lines() == [[""]]

        @pytest.mark.parametrize("text", ["", "a", "Hello"])
        def test_short_text_fits_within_limit(self, text):
            """Text shorter than or equal to line_limit stays on one line."""
            line_limit = 5
            assert len(text) <= line_limit  # Make sure Test is valid
            editor = TextEditor(line_limit=line_limit, text=text)
            assert editor.text == text
            assert editor.get_lines() == [text]
            assert editor.get_sub_lines() == [[text]]

        def test_text_equal_to_line_limit(self):
            """Text exactly equal to line_limit should remain on one line."""
            text = "Hello"  # len = 5
            editor = TextEditor(line_limit=len(text), text=text)
            assert editor.get_lines() == [text]

        def test_long_text_wraps_across_lines(self):
            """Text longer than line_limit should wrap into multiple lines."""
            text = "Hello!"
            editor = TextEditor(line_limit=len("Hello"), text=text)
            assert editor.text == text
            assert editor.get_lines() == ["Hello", "!"]
            assert editor.get_sub_lines() == [["Hello", "!"]]

        def test_multi_line_text_with_blank_line(self):
            """Newlines in text should create explicit empty lines."""
            text = "Hello!\n\nWorld"
            editor = TextEditor(line_limit=len("Hello"), text=text)
            assert editor.get_lines() == ["Hello", "!", "", "World"]
            assert editor.get_sub_lines() == [["Hello", "!"], [""], ["World"]]

        def test_trailing_newline(self):
            """Trailing newline should add an empty last line."""
            text = "Hello\n"
            editor = TextEditor(line_limit=10, text=text)
            assert editor.get_lines() == ["Hello", ""]

        def test_multiple_consecutive_newlines(self):
            """Multiple consecutive newlines should create multiple empty lines."""
            text = "\n\n"
            editor = TextEditor(line_limit=10, text=text)
            assert editor.get_lines() == ["", "", ""]

        def test_whitespace_only_text(self):
            """Whitespace-only text should be preserved."""
            line_limit = 10
            text = " " * line_limit
            editor = TextEditor(line_limit=line_limit, text=text)
            assert editor.get_lines() == [text]

        def test_newline_only_text(self):
            """Newline-only text should be preserved."""
            n = 5
            text = "\n" * n
            editor = TextEditor(line_limit=10, text=text)
            assert editor.get_lines() == ["" for _ in range(n + 1)]

        def test_tab_only_text(self):
            """Tabs are replaced with spaces."""
            line_limit = 10
            text = "\t" * 2
            editor = TextEditor(line_limit=line_limit, text=text)
            assert editor.get_lines() == [text]

        def test_long_word_wrapping(self):
            """Very long word should wrap without hyphenation."""
            text = "Supercalifragilisticexpialidocious"
            editor = TextEditor(line_limit=10, text=text)
            lines = editor.get_lines()
            assert all(len(line) <= 10 for line in lines)

        def test_unicode_characters(self):
            """Unicode text should wrap correctly without breaking characters."""
            text = "你好世界"
            editor = TextEditor(line_limit=2, text=text)
            assert editor.get_lines() == ["你好", "世界"]

        @pytest.mark.parametrize("text", [
            0, 0.0, ["Hello", "World"], [["Hello", "World"], ["Test"]], {"text": "Hello"}
        ])
        def test_invalid_text_type(self, text):
            """Non-str/None text should raise TypeError."""
            with pytest.raises(TypeError,
                               match="must be of type str or None"):
                TextEditor(line_limit=10, text=text)

        def test_text_read_only(self):
            """TextEditor.text should be read-only for assignment."""
            editor = TextEditor(line_limit=10, text="Hello")
            # Assigning text should raise an AttributeError
            with pytest.raises(AttributeError,
                               match="has no setter"):
                editor.text = "World"

        def test_text_deleter_resets_state(self):
            """Deleting text should clear editor state but preserve line_limit."""
            editor = TextEditor(line_limit=10, text="Hello")
            assert editor.text == "Hello"

            # Delete text
            del editor.text

            # Text is reset
            assert editor.text == ""
            assert editor.get_lines() == [""]
            assert editor.get_sub_lines() == [[""]]

            # Cursor should reset to origin
            assert editor.cursor == (0, 0)

            # Line limit should be preserved
            assert editor.line_limit == 10

        def test_text_deleter_idempotent(self):
            """Deleting text multiple times should be safe (idempotent)."""
            editor = TextEditor(line_limit=10, text="Hello")

            del editor.text
            assert editor.text == ""

            # Second delete should not error
            del editor.text
            assert editor.text == ""


class TestLineLimit:
    @pytest.mark.parametrize("line_limit", [1, 2, int(1e10)])
    def test_line_limit_setter_accepts_positive_integers(self, line_limit):
        """Setter should accept positive integers."""
        editor = TextEditor(line_limit=10)
        editor.line_limit = line_limit
        assert editor.line_limit == line_limit

    def test_line_limit_setter_shrinks_wrapping(self):
        """Shrinking line_limit should re-wrap lines."""
        editor = TextEditor(line_limit=10, text="Hello World!")

        assert editor.get_sub_lines() == [["Hello Worl", "d!"]]

        editor.line_limit = 5
        assert editor.get_sub_lines() == [["Hello", " Worl", "d!"]]

    def test_line_limit_setter_shrinks_with_newlines(self):
        """Shrinking line_limit should re-wrap lines with explicit newlines."""
        editor = TextEditor(line_limit=10, text="Hello\nWorld!")

        assert editor.get_sub_lines() == [["Hello"], ["World!"]]

        editor.line_limit = 5
        assert editor.get_sub_lines() == [["Hello"], ["World", "!"]]

    def test_line_limit_setter_expands_wrapping(self):
        """Expanding line_limit should reduce wrapping."""
        editor = TextEditor(line_limit=10, text="Hello World!")

        assert editor.get_sub_lines() == [["Hello Worl", "d!"]]

        editor.line_limit = 20
        assert editor.get_sub_lines() == [["Hello World!"]]

    def test_line_limit_setter_expands_with_newlines(self):
        """Expanding line_limit should not merge across newlines."""
        editor = TextEditor(line_limit=10, text="Hello\nWorld!")

        assert editor.get_sub_lines() == [["Hello"], ["World!"]]

        editor.line_limit = 20
        assert editor.get_sub_lines() == [["Hello"], ["World!"]]

    @pytest.mark.parametrize("line_limit", [-100, -1, 0])
    def test_line_limit_setter_rejects_non_positive_integers(self, line_limit):
        """line_limit <= 0 should raise ValueError."""
        editor = TextEditor(line_limit=10)
        with pytest.raises(ValueError,
                           match="line_limit must be greater than 0"):
            editor.line_limit = line_limit

    @pytest.mark.parametrize("line_limit", ["a", None, 2.0, [], {}, float("inf"), float("nan")])
    def test_line_limit_setter_rejects_invalid_types(self, line_limit):
        """Non-int types should raise TypeError."""
        editor = TextEditor(line_limit=10)
        with pytest.raises(TypeError,
                           match="line_limit must be of type int"):
            editor.line_limit = line_limit

    def test_line_limit_deleter_not_allowed(self):
        """line_limit should not be deletable."""
        editor = TextEditor(line_limit=10, text="Hello")
        with pytest.raises(AttributeError,
                           match="has no deleter"):
            del editor.line_limit

    def test_line_limit_setter_min_value(self):
        """line_limit=1 should wrap to single characters."""
        editor = TextEditor(line_limit=1, text="Hi!")
        assert editor.get_sub_lines() == [["H", "i", "!"]]

    def test_line_limit_setter_reset_back_and_forth(self):
        """Shrinking then expanding back should restore wrapping."""
        editor = TextEditor(line_limit=10, text="Hello World!")
        assert editor.get_sub_lines() == [["Hello Worl", "d!"]]

        editor.line_limit = 5
        assert editor.get_sub_lines() == [["Hello", " Worl", "d!"]]

        editor.line_limit = 10
        assert editor.get_sub_lines() == [["Hello Worl", "d!"]]

    def test_line_limit_setter_on_empty_text(self):
        """Resizing line_limit on empty text should keep empty state."""
        editor = TextEditor(line_limit=10, text="")
        editor.line_limit = 5
        assert editor.get_sub_lines() == [[""]]

    def test_line_limit_setter_no_change(self):
        """Resizing line_limit to same value should not change wrapping."""
        editor = TextEditor(line_limit=10, text="Hello World!")
        assert editor.get_sub_lines() == [["Hello Worl", "d!"]]

        editor.line_limit = 10
        assert editor.get_sub_lines() == [["Hello Worl", "d!"]]


class TestCursor:
    class TestCursorNoText:
        """Test the cursor parameter"""

        @pytest.mark.parametrize("line, char", [(1, 2), [3, 4]])
        def test_empty_text_with_cursor_types(self, line, char):
            """List and tuple cursor should be converted to tuple."""
            editor = TextEditor(line_limit=10)
            assert editor.text == ""
            editor.cursor = line, char
            assert editor.cursor == (0, 0)
            assert editor.line_cursor == (0, 0)

        @pytest.mark.parametrize("char", [0, 1, int(1e10)])
        @pytest.mark.parametrize("line", [0, 1, int(1e10)])
        def test_empty_text_with_cursor_values(self, line, char):
            """Cursor beyond bounds should reset to (0, 0), with no text."""
            editor = TextEditor(line_limit=10)
            editor.cursor = (line, char)
            assert editor.text == ""
            # Clamp to 0, 0
            assert editor.cursor == (0, 0)
            assert editor.line_cursor == (0, 0)

        @pytest.mark.parametrize("line, char", [(-1, -1), (-1, 0), (0, -1)])
        def test_empty_text_with_invalid_cursor(self, line, char):
            """Negative cursor is not allowed. Should raise ValueError."""
            editor = TextEditor(line_limit=10)
            with pytest.raises(ValueError,
                               match="must be non-negative"):
                editor.cursor = line, char

        @pytest.mark.parametrize("cursor", ["a", {"line": 1, "char": 2}])
        def test_invalid_cursor_type(self, cursor):
            editor = TextEditor(line_limit=10)
            with pytest.raises(TypeError,
                               match="must be of type tuple"):
                editor.cursor = cursor

        @pytest.mark.parametrize("cursor", [(1, 2, 3), (1,)])
        def test_invalid_cursor_length(self, cursor):
            editor = TextEditor(line_limit=10)
            with pytest.raises(ValueError,
                               match="must be of length 2"):
                editor.cursor = cursor

        @pytest.mark.parametrize("line, char", [(1, "a"), ("a", 0)])
        def test_invalid_cursor_value_type(self, line, char):
            editor = TextEditor(line_limit=10)
            with pytest.raises(TypeError,
                               match="must be of type int"):
                editor.cursor = line, char

        @pytest.mark.parametrize("line, char", [(1.0, 0), (0, 2.0)])
        def test_invalid_cursor_value_float(self, line, char):
            """Float values are not allowed for cursor."""
            editor = TextEditor(line_limit=10)
            with pytest.raises(TypeError,
                               match="must be of type int"):
                editor.cursor = line, char

        @pytest.mark.parametrize("line, char", [(True, 0), (0, False)])
        def test_invalid_cursor_value_bool(self, line, char):
            """Bool values should be rejected (even though bool is a subclass of int)."""
            editor = TextEditor(line_limit=10)
            with pytest.raises(TypeError,
                               match="must be of type int"):
                editor.cursor = line, char

        def test_cursor_idempotence(self):
            """Setting cursor=(0, 0) repeatedly should not change state."""
            editor = TextEditor(line_limit=10)
            editor.cursor = (0, 0)
            assert editor.cursor == (0, 0)
            assert editor.line_cursor == (0, 0)

            # Repeat assignment
            editor.cursor = (0, 0)
            assert editor.cursor == (0, 0)
            assert editor.line_cursor == (0, 0)

        def test_cursor_deleter_not_allowed(self):
            """cursor should not be deletable."""
            editor = TextEditor(line_limit=10)
            with pytest.raises(AttributeError,
                               match="has no deleter"):
                del editor.cursor

        def test_line_cursor_setter_not_allowed(self):
            """cursor should not be deletable."""
            editor = TextEditor(line_limit=10)
            with pytest.raises(AttributeError,
                               match="has no setter"):
                editor.line_cursor = (0, 0)

        def test_line_cursor_deleter_not_allowed(self):
            """cursor should not be deletable."""
            editor = TextEditor(line_limit=10)
            with pytest.raises(AttributeError,
                               match="has no deleter"):
                del editor.line_cursor

    class TestCursorWithText:
        """Test the cursor parameter with text."""

        @pytest.mark.parametrize("text", ["", "\n", "Hello", "Hello World!", "Hello\nWorld! How are you doing?"])
        def test_cursor_default(self, text):
            """
            By default, the ``cursor`` should be placed at the end of the display text (display coords).
            """
            line_limit = 10
            editor = TextEditor(line_limit=line_limit, text=text)

            display_lines = editor.get_lines()
            display_line_nr = len(display_lines) - 1
            display_line_len = len(display_lines[-1])

            assert editor.cursor == (display_line_nr, display_line_len)
            # assert editor.line_cursor == (0, len(text))  # No newlines!
            # assert "\n" not in text

        @pytest.mark.parametrize("text", ["", "Hello", "Hello World!", "Hello World! How are you doing?"])
        def test_line_cursor_default(self, text):
            """
            By default, the ``line_cursor`` should point to the end of the last logical line.
            No newlines characters = One logical line.
            """
            line_limit = 10
            editor = TextEditor(line_limit=line_limit, text=text)

            # assert editor.cursor == (display_line_nr, display_line_len)
            assert editor.line_cursor == (0, len(editor.text))  # No newlines!
            assert "\n" not in text

        @pytest.mark.parametrize("text", ["\n", "Hello\n", "\nHello\nWorld!", "Hello\nWorld! How are you doing?"])
        def test_cursor_default_with_newline(self, text):
            """
            By default, ``line_cursor`` should point to the end of the last logical line.
            """
            line_limit = 10
            editor = TextEditor(line_limit=line_limit, text=text)

            logic_lines = text.split("\n")
            logic_line_nr = len(logic_lines) - 1
            logic_line_len = len(logic_lines[-1])

            # assert editor.cursor == (display_line_nr, display_line_len)
            assert editor.line_cursor == (logic_line_nr, logic_line_len)
            assert "\n" in text

        @pytest.mark.parametrize("char", [0, 3, 6])
        @pytest.mark.parametrize("line", [0, 1, 2])
        def test_set_cursor(self, line, char):
            """
            Test setting ``cursor`` to ``(line,char)``.

            Tests:
              - Start of each line  ``(line,0)``
              - Middle of each line ``(line,3)``
              - End of each line    ``(line,6)``
            """
            text = "Line 1\nLine 2\nLine 3"
            editor = TextEditor(line_limit=10, text=text)

            lines = editor.get_lines()
            assert lines == text.split("\n")  # Make sure Test cases are valid (Display lines == logic lines)

            line_nr = len(lines) - 1  # Zero-indexed last line
            line_len = len(lines[line_nr])  # Length of last line
            end_of_file = (line_nr, line_len)

            assert all(len(line) >= char for line in lines)  # Make sure Test cases are valid

            # Cursor starts at end of text by default.
            assert editor.cursor == end_of_file
            assert editor.line_cursor == end_of_file

            editor.cursor = end_of_file
            assert editor.cursor == end_of_file
            assert editor.line_cursor == end_of_file

        @pytest.mark.parametrize("line, char", [
            (0, 100),
            (1, 100)
        ])
        def test_set_cursor_out_of_line_bounds(self, line, char):
            """Test setting ``cursor`` to ``(line,char)`` out of bounds. Clamp to line length."""
            text = "Line 1\nLine 2\nLine 3"
            editor = TextEditor(line_limit=10, text=text)

            out_of_bounds = (line, char)

            lines = editor.get_lines()
            assert lines == text.split("\n")  # Make sure Test cases are valid (Display lines == logic lines)

            line_nr = len(lines) - 1  # Zero-indexed last line
            line_len = len(lines[line_nr])  # Length of last line
            end_of_file = (line_nr, line_len)

            assert editor.cursor == end_of_file
            assert editor.line_cursor == end_of_file

            # Cursor should not go out of bounds
            editor.cursor = out_of_bounds
            assert editor.cursor == (line + 1, len(lines[line + 1]))
            assert editor.line_cursor == (line + 1, len(lines[line + 1]))

        @pytest.mark.parametrize("line, char", [
            (2, 100),
            (100, 100)
        ])
        def test_set_cursor_out_of_text_bounds(self, line, char):
            """Test setting ``cursor`` to ``(line,char)`` out of bounds. Clamp to line length and text length."""
            text = "Line 1\nLine 2\nLine 3"
            editor = TextEditor(line_limit=10, text=text)

            out_of_bounds = (line, char)

            lines = editor.get_lines()
            assert lines == text.split("\n")  # Make sure Test cases are valid (Display lines == logic lines)

            line_nr = len(lines) - 1  # Zero-indexed last line
            line_len = len(lines[line_nr])  # Length of last line
            end_of_file = (line_nr, line_len)

            assert editor.cursor == end_of_file
            assert editor.line_cursor == end_of_file

            # Cursor should not go out of bounds
            editor.cursor = out_of_bounds
            assert editor.cursor == end_of_file
            assert editor.line_cursor == end_of_file


class TestCursorMovement:
    class TestMoveLeft(AbstractTestHorizontalMove):

        def test_move_in_empty_text(self):
            editor, text = editor_factory()

            editor.move_left()
            assert editor.cursor == (0, 0)
            assert editor.line_cursor == (0, 0)

            assert editor.text == ""

        def test_move_within_display_line(self):
            text = "Hello World!"
            char = 5
            editor, text = editor_factory(text, cursor=(0, char))

            editor.move_left()
            assert editor.cursor == (0, char - 1)
            assert editor.line_cursor == (0, char - 1)

            # movement must not change text
            assert editor.text == text

        def test_multi_move_within_display_line(self):
            text = "Hello World!"
            char = 5
            multi = 3

            editor, text = editor_factory(text, cursor=(0, char))

            for _ in range(multi):
                editor.move_left()
            assert editor.cursor == (0, char - multi)
            assert editor.line_cursor == (0, char - multi)

            # movement must not change text
            assert editor.text == text

        def test_move_across_newline(self):
            text = "Hello\nWorld!"
            editor, text = editor_factory(text, cursor=(1, 0))

            editor.move_left()
            assert editor.cursor == (0, len("Hello"))
            assert editor.line_cursor == (0, len("Hello"))

            # movement must not change text
            assert editor.text == text

        def test_cursor_moves_across_wrapped_line(self):
            line_limit = 10
            editor, text = editor_factory("Hello World!", line_limit=line_limit, cursor=(1, 0))

            editor.move_left()
            assert editor.cursor == (0, line_limit - 1)
            assert editor.line_cursor == (0, line_limit - 1)

            # movement must not change text
            assert editor.text == text

        def test_move_out_of_bounds(self):
            editor, text = editor_factory("Hello World!", cursor=(0, 0))

            editor.move_left()
            assert editor.cursor == (0, 0)
            assert editor.line_cursor == (0, 0)

            # movement must not change text
            assert editor.text == text

        def test_move_from_empty_line(self):
            editor, text = editor_factory("Hello\n\nWorld!", cursor=(1, 0))

            editor.move_left()
            assert editor.cursor == (0, len("Hello"))
            assert editor.line_cursor == (0, len("Hello"))

            # movement must not change text
            assert editor.text == text

        def test_move_to_empty_line(self):
            editor, text = editor_factory("Hello\n\nWorld!", cursor=(2, 0))

            editor.move_left()
            assert editor.cursor == (1, 0)
            assert editor.line_cursor == (1, 0)

            # movement must not change text
            assert editor.text == text

        def test_move_when_line_wraps_exact_boundary(self):
            line_limit = 10
            editor, text = editor_factory("01234567890123456789", line_limit=line_limit, cursor=(1, line_limit))

            editor.move_left()
            assert editor.cursor == (1, line_limit - 1)
            assert editor.line_cursor == (0, line_limit * 2 - 1)

            # movement must not change text
            assert editor.text == text

        def test_move_multi_logic_line_document(self):
            editor, text = editor_factory("Hel\nlo \nWor\nld!", cursor=(3, 0))

            assert editor.get_lines()[3] == "ld!"

            for _ in range(6):
                editor.move_left()
            assert editor.cursor == (1, 2)
            assert editor.get_lines()[1] == "lo "

            # movement must not change text
            assert editor.text == text

        def test_move_multi_display_line_document(self):
            editor, text = editor_factory("Hello World!", line_limit=3, cursor=(3, 0))

            assert editor.get_lines()[3] == "ld!"

            for _ in range(6):
                editor.move_left()
            assert editor.cursor == (1, 0)
            assert editor.get_lines()[1] == "lo "

            # movement must not change text
            assert editor.text == text

        def test_move_multi_line_document(self):
            editor, text = editor_factory("Hello\nWorld!", line_limit=3, cursor=(3, 0))

            assert editor.get_lines()[3] == "ld!"

            for _ in range(6):
                editor.move_left()
            assert editor.cursor == (1, 0)
            assert editor.get_lines()[1] == "lo"

            # movement must not change text
            assert editor.text == text

    class TestMoveRight(AbstractTestHorizontalMove):
        def test_move_in_empty_text(self):
            editor, text = editor_factory()

            editor.move_right()
            assert editor.cursor == (0, 0)
            assert editor.line_cursor == (0, 0)

            # movement must not change text
            assert editor.text == text

        def test_move_within_display_line(self):
            editor, text = editor_factory("Hello World!", cursor=(0, len("He")))

            editor.move_right()
            assert editor.cursor == (0, len("Hel"))
            assert editor.line_cursor == (0, len("Hel"))

        def test_multi_move_within_display_line(self):
            char = 5
            multi = 3

            editor, text = editor_factory("Hello World!", cursor=(0, char))

            for _ in range(multi):
                editor.move_right()
            assert editor.cursor == (0, char + multi)
            assert editor.line_cursor == (0, char + multi)

            # movement must not change text
            assert editor.text == text

        def test_move_across_newline(self):
            editor, text = editor_factory("Hello\nWorld!", cursor=(0, len("Hello")))

            editor.move_right()
            assert editor.cursor == (1, 0)
            assert editor.line_cursor == (1, 0)

            # movement must not change text
            assert editor.text == text

        def test_cursor_moves_across_wrapped_line(self):
            line_limit = 10
            editor, text = editor_factory("Hello World!", line_limit=line_limit, cursor=(0, line_limit - 1))

            editor.move_right()
            assert editor.cursor == (1, 0)
            assert editor.line_cursor == (0, line_limit)

            # movement must not change text
            assert editor.text == text

        def test_move_out_of_bounds(self):
            editor, text = editor_factory("Hello World!", cursor=(1, 2))

            editor.move_right()
            assert editor.cursor == (1, 2)
            assert editor.line_cursor == (0, 12)

            # movement must not change text
            assert editor.text == text

        def test_move_from_empty_line(self):
            editor, text = editor_factory("Hello\n\nWorld!", cursor=(1, 0))

            editor.move_right()
            assert editor.cursor == (2, 0)
            assert editor.line_cursor == (2, 0)

            # movement must not change text
            assert editor.text == text

        def test_move_to_empty_line(self):
            editor, text = editor_factory("Hello\n\nWorld!", cursor=(0, len("Hello")))

            editor.move_right()
            assert editor.cursor == (1, 0)
            assert editor.line_cursor == (1, 0)

            # movement must not change text
            assert editor.text == text

        def test_move_when_line_wraps_exact_boundary(self):
            line_limit = 10
            editor, text = editor_factory("01234567890123456789", line_limit=line_limit, cursor=(1, line_limit))

            editor.move_right()
            assert editor.cursor == (1, line_limit)
            assert editor.line_cursor == (0, line_limit * 2)

            # movement must not change text
            assert editor.text == text

        def test_move_multi_logic_line_document(self):
            editor, text = editor_factory("Hel\nlo \nWor\nld!", cursor=(0, 3))

            assert editor.get_lines()[0] == "Hel"

            for _ in range(6):
                editor.move_right()
            assert editor.cursor == (2, 1)
            assert editor.get_lines()[2] == "Wor"

            # movement must not change text
            assert editor.text == text

        def test_move_multi_display_line_document(self):
            line_limit = 3
            editor, text = editor_factory("Hello World!", line_limit=line_limit, cursor=(0, line_limit))

            assert editor.get_lines()[0] == "Hel"

            for _ in range(6):
                editor.move_right()
            assert editor.cursor == (3, 0)
            assert editor.get_lines()[3] == "ld!"

            # movement must not change text
            assert editor.text == text

        def test_move_multi_line_document(self):
            line_limit = 3
            editor, text = editor_factory("Hello\nWorld!", line_limit=line_limit, cursor=(0, line_limit))

            assert editor.get_lines()[0] == "Hel"

            for _ in range(6):
                editor.move_right()
            assert editor.cursor == (3, 0)
            assert editor.get_lines()[3] == "ld!"

            # movement must not change text
            assert editor.text == text

    class TestMoveUp(AbstractTestVerticalMove):

        def test_move_in_empty_text(self):
            editor, text = editor_factory()

            editor.move_up()
            assert editor.cursor == (0, 0)
            assert editor.line_cursor == (0, 0)

            # movement must not change text
            assert editor.text == text

        def test_move_between_display_lines(self):
            editor, text = editor_factory("Hello World!", cursor=(1, 1))

            editor.move_up()
            assert editor.cursor == (0, 1)
            assert editor.line_cursor == (0, 1)

            # movement must not change text
            assert editor.text == text

        def test_move_across_newline(self):
            char = 3
            editor, text = editor_factory("Hello\nWorld!", cursor=(1, char))

            editor.move_up()
            assert editor.cursor == (0, char)
            assert editor.line_cursor == (0, char)

            # movement must not change text
            assert editor.text == text

        def test_move_out_of_bounds(self):
            editor, text = editor_factory("Hello World!", cursor=(0, 0))

            editor.move_up()
            assert editor.cursor == (0, 0)
            assert editor.line_cursor == (0, 0)

            # movement must not change text
            assert editor.text == text

        def test_move_from_empty_line(self):
            editor, text = editor_factory("Hello\n\nWorld!", cursor=(1, 0))

            editor.move_up()
            assert editor.cursor == (0, 0)
            assert editor.line_cursor == (0, 0)

            # movement must not change text
            assert editor.text == text

        def test_move_to_empty_line(self):
            editor, text = editor_factory("Hello\n\nWorld!", cursor=(2, len("Wor")))

            editor.move_up()
            assert editor.cursor == (1, 0)
            assert editor.line_cursor == (1, 0)

            # movement must not change text
            assert editor.text == text

        def test_move_when_line_wraps_exact_boundary(self):
            line_limit = 10
            editor, text = editor_factory("01234567890123456789", line_limit=line_limit, cursor=(1, line_limit))

            editor.move_up()
            assert editor.cursor == (1, 0)
            assert editor.line_cursor == (0, line_limit)

            # movement must not change text
            assert editor.text == text

        def test_move_multi_logic_line_document(self):
            editor, text = editor_factory("Hel\nlo \nWor\nld!", cursor=(2, 1))

            editor.move_up()
            assert editor.cursor == (1, 1)
            assert editor.line_cursor == (1, 1)

            editor.move_up()
            assert editor.cursor == (0, 1)
            assert editor.line_cursor == (0, 1)

            # movement must not change text
            assert editor.text == text

        def test_move_multi_display_line_document(self):
            line_limit = 3
            editor, text = editor_factory("Hello World!", line_limit=line_limit, cursor=(2, 1))

            assert editor.cursor == (2, 1)
            assert editor.line_cursor == (0, line_limit * 2 + 1)

            editor.move_up()
            assert editor.cursor == (1, 1)
            assert editor.line_cursor == (0, line_limit + 1)

            editor.move_up()
            assert editor.cursor == (0, 1)
            assert editor.line_cursor == (0, 1)

            # movement must not change text
            assert editor.text == text

        def test_move_multi_line_document(self):
            line_limit = 3
            editor, text = editor_factory("Hello\nWorld!", line_limit=line_limit, cursor=(3, 1))

            assert editor.cursor == (3, 1)
            assert editor.line_cursor == (1, line_limit + 1)

            editor.move_up()
            assert editor.cursor == (2, 1)
            assert editor.line_cursor == (1, 1)

            editor.move_up()
            assert editor.cursor == (1, 1)
            assert editor.line_cursor == (0, line_limit + 1)

            editor.move_up()
            assert editor.cursor == (0, 1)
            assert editor.line_cursor == (0, 1)

            # movement must not change text
            assert editor.text == text

        def test_move_on_first_display_line(self):
            editor, text = editor_factory("Hello\nWorld!", cursor=(0, 3))

            editor.move_up()
            assert editor.cursor == (0, 0)
            assert editor.line_cursor == (0, 0)

            # movement must not change text
            assert editor.text == text

        def test_move_on_last_display_line(self):
            editor, text = editor_factory("Hello\nWorld!", cursor=(1, 3))

            editor.move_up()
            assert editor.cursor == (0, 3)
            assert editor.line_cursor == (0, 3)

            # movement must not change text
            assert editor.text == text

    class TestMoveDown(AbstractTestVerticalMove):

        def test_move_in_empty_text(self):
            editor, text = editor_factory()

            editor.move_down()
            assert editor.cursor == (0, 0)
            assert editor.line_cursor == (0, 0)

            # movement must not change text
            assert editor.text == text

        def test_move_between_display_lines(self):
            editor, text = editor_factory("Hello World!", cursor=(0, 1))

            editor.move_down()
            assert editor.cursor == (1, 1)
            assert editor.line_cursor == (0, 11)

            # movement must not change text
            assert editor.text == text

        def test_move_across_newline(self):
            char = 3
            editor, text = editor_factory("Hello\nWorld!", cursor=(0, char))

            editor.move_down()
            assert editor.cursor == (1, char)
            assert editor.line_cursor == (1, char)

            # movement must not change text
            assert editor.text == text

        def test_move_out_of_bounds(self):
            editor, text = editor_factory("Hello World!", cursor=(1, 2))

            editor.move_down()
            assert editor.cursor == (1, 2)
            assert editor.line_cursor == (0, len("Hello World!"))

            # movement must not change text
            assert editor.text == text

        def test_move_from_empty_line(self):
            editor, text = editor_factory("Empty line\n\nWorld!", cursor=(1, 0))

            editor.move_down()
            assert editor.cursor == (2, 0)
            assert editor.line_cursor == (2, 0)

            # movement must not change text
            assert editor.text == text

        def test_move_to_empty_line(self):
            editor, text = editor_factory("Hello\n\nWorld!", cursor=(0, len("Hello")))

            editor.move_down()
            assert editor.cursor == (1, 0)
            assert editor.line_cursor == (1, 0)

            # movement must not change text
            assert editor.text == text

        def test_move_when_line_wraps_exact_boundary(self):
            line_limit = 10
            editor, text = editor_factory("01234567890123456789", line_limit=line_limit, cursor=(1, line_limit))

            editor.move_down()
            assert editor.cursor == (1, line_limit)
            assert editor.line_cursor == (0, line_limit * 2)

            # movement must not change text
            assert editor.text == text

        def test_move_multi_logic_line_document(self):
            editor, text = editor_factory("Hel\nlo \nWor\nld!", cursor=(0, 1))

            assert editor.cursor == (0, 1)
            assert editor.line_cursor == (0, 1)

            editor.move_down()
            assert editor.cursor == (1, 1)
            assert editor.line_cursor == (1, 1)

            editor.move_down()
            assert editor.cursor == (2, 1)
            assert editor.line_cursor == (2, 1)

            # movement must not change text
            assert editor.text == text

        def test_move_multi_display_line_document(self):
            line_limit = 3
            editor, text = editor_factory("Hello World!", line_limit=line_limit, cursor=(0, 1))

            assert editor.cursor == (0, 1)
            assert editor.line_cursor == (0, 1)

            editor.move_down()
            assert editor.cursor == (1, 1)
            assert editor.line_cursor == (0, line_limit + 1)

            editor.move_down()
            assert editor.cursor == (2, 1)
            assert editor.line_cursor == (0, line_limit * 2 + 1)

            editor.move_down()
            assert editor.cursor == (3, 1)
            assert editor.line_cursor == (0, line_limit * 3 + 1)

            # movement must not change text
            assert editor.text == text

        def test_move_multi_line_document(self):
            line_limit = 3
            editor, text = editor_factory("Hello\nWorld!", line_limit=line_limit, cursor=(0, 1))

            assert editor.cursor == (0, 1)
            assert editor.line_cursor == (0, 1)

            editor.move_down()
            assert editor.cursor == (1, 1)
            assert editor.line_cursor == (0, line_limit + 1)

            editor.move_down()
            assert editor.cursor == (2, 1)
            assert editor.line_cursor == (1, 1)

            editor.move_down()
            assert editor.cursor == (3, 1)
            assert editor.line_cursor == (1, line_limit + 1)

            # movement must not change text
            assert editor.text == text

        def test_move_on_first_display_line(self):
            editor, text = editor_factory("Hello\nWorld!", cursor=(0, 3))

            editor.move_down()
            assert editor.cursor == (1, 3)
            assert editor.line_cursor == (1, 3)

            # movement must not change text
            assert editor.text == text

        def test_move_on_last_display_line(self):
            editor, text = editor_factory("Hello\nWorld!", cursor=(1, 3))

            editor.move_down()
            assert editor.cursor == (1, len("World!"))
            assert editor.line_cursor == (1, len("World!"))

            # movement must not change text
            assert editor.text == text

    @pytest.mark.parametrize(
        "cursor",
        [(0, 0), (1, 1), (2, 2), (10, 10)])
    # some cursors will be out of bounds, should clamp to valid position
    @pytest.mark.parametrize(
        "text",
        ["", "\n", "Hello", "Hello World!", "Hello\nWorld! How are you doing?"],
    )
    def test_move_home(self, text, cursor):
        """``move_home`` always moves the cursor to the beginning of the text. (0, 0)"""
        editor, text = editor_factory(text, cursor=cursor)

        editor.move_home()

        assert editor.cursor == (0, 0)
        assert editor.line_cursor == (0, 0)

        # movement must not change text
        assert editor.text == text

    @pytest.mark.parametrize(
        "cursor",
        [(0, 0), (1, 1), (2, 2), (10, 10)])
    # some cursors will be out of bounds, should clamp to valid positions
    @pytest.mark.parametrize(
        "text",
        ["", "\n", "Hello", "Hello World!", "Hello\nWorld! How are you doing?"],
    )
    def test_move_end(self, text, cursor):
        """``move_end`` always moves the cursor to the end of the text."""
        editor, text = editor_factory(text, cursor=cursor)

        editor.move_end()

        display_lines = editor.get_lines()
        display_line_nr = len(display_lines) - 1
        display_line_len = len(display_lines[-1])

        logic_lines = editor.text.split("\n")
        logic_line_nr = len(logic_lines) - 1
        logic_line_len = len(logic_lines[-1])

        assert editor.cursor == (display_line_nr, display_line_len)
        assert editor.line_cursor == (logic_line_nr, logic_line_len)

        # movement must not change text
        assert editor.text == text


class TestInsert:
    class TestInsertNoChar:
        @pytest.mark.parametrize(
            "char",
            [0, 5, 12]
        )
        def test_insert_nothing(self, char):
            """Inserting nothing should not change the text or the cursor position."""
            editor, text = editor_factory("Hello World!", cursor=(0, char), line_limit=100)

            editor.insert("")

            assert editor.text == text
            assert editor.get_lines() == [text]
            assert editor.get_sub_lines() == [[text]]
            assert editor.cursor == (0, char)

        @pytest.mark.parametrize(
            "text",
            [None, 1234, 3.1415, [1, 2, 3], {"a": 1, "b": 2}, True]
        )
        def test_insert_invalid_type(self, text):
            editor, _ = editor_factory("Hello World!")

            with pytest.raises(TypeError,
                               match="must be of type str"):
                editor.insert(text)

    class TestInsertChar:
        """Test inserting a single character."""

        class TestInsertRegularCharacter:
            def test_insert_char_end(self):
                """Inserting a character at the end of the text should advance the cursor."""
                editor, text = editor_factory("Hello World", line_limit=100)

                editor.insert("!")

                target_text = text + "!"
                assert editor.text == target_text
                assert editor.get_lines() == [target_text]
                assert editor.get_sub_lines() == [[target_text]]
                assert editor.cursor == (0, len(target_text))

            def test_insert_char_middle(self):
                char = 5
                editor, text = editor_factory("HelloWorld!", cursor=(0, char), line_limit=100)

                editor.insert(" ")

                target_text = text[:char] + " " + text[char:]
                assert editor.text == target_text
                assert editor.get_lines() == [target_text]
                assert editor.get_sub_lines() == [[target_text]]
                assert editor.cursor == (0, 6)

            def test_insert_char_home(self):
                editor, text = editor_factory("ello World!", cursor=(0, 0), line_limit=100)

                editor.insert("H")

                target_text = "H" + text
                assert editor.text == target_text
                assert editor.get_lines() == [target_text]
                assert editor.get_sub_lines() == [[target_text]]
                assert editor.cursor == (0, 1)

            def test_insert_char_at_limit(self):
                text = "Hello World!"
                editor, text = editor_factory(text, line_limit=len(text))

                editor.insert("!")

                assert editor.text == text + "!"
                assert editor.get_lines() == [text, "!"]
                assert editor.get_sub_lines() == [[text, "!"]]

                assert editor.cursor == (1, 1)
                assert editor.line_cursor == (0, len(text) + 1)

            def testInsert_char_into_empty_text(self):
                editor, text = editor_factory(line_limit=100)

                editor.insert("H")

                target_text = "H"
                assert editor.text == target_text
                assert editor.get_lines() == [target_text]
                assert editor.get_sub_lines() == [[target_text]]
                assert editor.cursor == (0, 1)
                assert editor.line_cursor == (0, 1)

            def test_insert_char_before_newline(self):
                char = len("Hello")
                editor, text = editor_factory("Hello\nWorld!", cursor=(0, char), line_limit=100)

                editor.insert("!")

                assert editor.text == "Hello!\nWorld!"
                assert editor.get_lines() == ["Hello!", "World!"]
                assert editor.get_sub_lines() == [["Hello!"], ["World!"]]

                assert editor.cursor == (0, char + 1)
                assert editor.line_cursor == (0, char + 1)

        class TestInsertNewline:

            def test_insert_newline_end(self):
                editor, text = editor_factory("Hello World!", line_limit=100)

                editor.insert("\n")

                assert editor.text == text + "\n"
                assert editor.get_lines() == ["Hello World!", ""]
                assert editor.get_sub_lines() == [["Hello World!"], [""]]

                assert editor.cursor == (1, 0)
                assert editor.line_cursor == (1, 0)

            def test_insert_newline_middle(self):
                char = len("Hello")
                editor, text = editor_factory("HelloWorld!", cursor=(0, char), line_limit=100)

                editor.insert("\n")

                assert editor.text == "Hello\nWorld!"
                assert editor.get_lines() == ["Hello", "World!"]
                assert editor.get_sub_lines() == [["Hello"], ["World!"]]

                assert editor.cursor == (1, 0)
                assert editor.line_cursor == (1, 0)

            def test_insert_newline_home(self):
                editor, text = editor_factory("Hello World!", cursor=(0, 0), line_limit=100)

                editor.insert("\n")

                assert editor.text == "\nHello World!"
                assert editor.get_lines() == ["", "Hello World!"]
                assert editor.get_sub_lines() == [[""], ["Hello World!"]]

                assert editor.cursor == (1, 0)
                assert editor.line_cursor == (1, 0)

            def test_insert_newline_at_limit(self):
                text = "Hello World!"
                editor, text = editor_factory(text, line_limit=len(text))

                editor.insert("\n")

                assert editor.text == text + "\n"
                assert editor.get_lines() == [text, ""]
                assert editor.get_sub_lines() == [[text], [""]]

                assert editor.cursor == (1, 0)
                assert editor.line_cursor == (1, 0)

            def test_insert_newline_in_long_text(self):
                text = "HelloWorld!"
                editor, text = editor_factory(text, line_limit=3, cursor=(0, len("Hello")))

                editor.insert("\n")

                assert editor.text == "Hello\nWorld!"
                assert editor.get_lines() == ["Hel", "lo", "Wor", "ld!"]
                assert editor.get_sub_lines() == [["Hel", "lo"], ["Wor", "ld!"]]

                assert editor.cursor == (2, 0)
                assert editor.line_cursor == (1, 0)

            def test_insert_newline_into_empty_text(self):
                editor, text = editor_factory(line_limit=100)

                editor.insert("\n")

                assert editor.text == "\n"
                assert editor.get_lines() == ["", ""]
                assert editor.get_sub_lines() == [[""], [""]]

                assert editor.cursor == (1, 0)
                assert editor.line_cursor == (1, 0)

        class TestInsertSpecialCharacter:
            # Insert special characters
            @pytest.mark.parametrize(
                "character",
                ["\\", "\'", "\"", "\t", " "]
            )
            def test_insert_special_char(self, character):
                # Insert character with no special effects
                char = len("Hello")
                editor, text = editor_factory("HelloWorld!", cursor=(0, char), line_limit=100)

                editor.insert(character)

                assert editor.text == f"Hello{character}World!"
                assert editor.get_lines() == [f"Hello{character}World!"]
                assert editor.get_sub_lines() == [[f"Hello{character}World!"]]

                assert editor.cursor == (0, char + 1)
                assert editor.line_cursor == (0, char + 1)

            @pytest.mark.parametrize(
                "character",
                ["\a", "\b", "\f", "\r", "\v"]
            )
            def test_insert_unsupported_special_char(self, character):
                editor, _ = editor_factory("Hello World!")

                with pytest.raises(UnsupportedCharacterError,
                                   match=f"Unsupported character: {character}"):
                    editor.insert(character)

    class TestInsertText:
        """Test inserting text."""

        class TestInsertRegularText:
            def test_insert_text_end(self):
                editor, text = editor_factory("Hello ", line_limit=100)

                editor.insert("World!")

                target_text = text + "World!"
                assert editor.text == target_text
                assert editor.get_lines() == [target_text]
                assert editor.get_sub_lines() == [[target_text]]

                assert editor.cursor == (0, len(target_text))
                assert editor.line_cursor == (0, len(target_text))

            def test_insert_text_middle(self):
                char = len("Hello")
                editor, text = editor_factory("Hello World!", cursor=(0, char), line_limit=100)

                editor.insert(" big")

                target_text = "Hello big World!"
                assert editor.text == target_text
                assert editor.get_lines() == [target_text]
                assert editor.get_sub_lines() == [[target_text]]

                assert editor.cursor == (0, char + len(" big"))
                assert editor.line_cursor == (0, char + len(" big"))

            def test_insert_text_home(self):
                editor, text = editor_factory("World!", cursor=(0, 0), line_limit=100)

                editor.insert("Hello ")

                target_text = "Hello " + text
                assert editor.text == target_text
                assert editor.get_lines() == [target_text]
                assert editor.get_sub_lines() == [[target_text]]

                assert editor.cursor == (0, len("Hello "))
                assert editor.line_cursor == (0, len("Hello "))

            def test_insert_text_at_limit(self):
                text = "Hello"
                insert_text = "World"
                editor, text = editor_factory(text, line_limit=len(text))

                editor.insert(insert_text)

                assert editor.text == text + insert_text
                assert editor.get_lines() == [text, insert_text]
                assert editor.get_sub_lines() == [[text, insert_text]]

                assert editor.cursor == (1, len(insert_text))
                assert editor.line_cursor == (0, len(text + insert_text))

            def test_insert_long_text_at_limit(self):
                text = "Hello"
                insert_text = " big World!"
                line_limit = 5
                editor, text = editor_factory("Hello", line_limit=line_limit)

                editor.insert(insert_text)
                assert editor.text == text + insert_text
                assert editor.get_lines() == [text, " big ", "World", "!"]
                assert editor.get_sub_lines() == [[text, " big ", "World", "!"]]

                assert editor.cursor == (3, 1)
                assert editor.line_cursor == (0, len(text + insert_text))

            def test_insert_text_into_empty_text(self):
                insert_text = "Hello World!"
                editor, text = editor_factory(line_limit=100)

                editor.insert(insert_text)

                assert editor.text == insert_text
                assert editor.get_lines() == [insert_text]
                assert editor.get_sub_lines() == [[insert_text]]

                assert editor.cursor == (0, len(insert_text))
                assert editor.line_cursor == (0, len(insert_text))

            def test_insert_text_into_empty_text_at_limit(self):
                insert_text = "Hello World!"
                line_limit = len(insert_text)
                editor, text = editor_factory(line_limit=line_limit)

                editor.insert(insert_text)

                assert editor.text == insert_text
                assert editor.get_lines() == [insert_text]
                assert editor.get_sub_lines() == [[insert_text]]

                assert editor.cursor == (0, len(insert_text))
                assert editor.line_cursor == (0, len(insert_text))

        class TestInsertTextWithSpecialCharacters:
            @pytest.mark.parametrize(
                "character",
                ["\a", "\b", "\f", "\r", "\v"]
            )
            def test_insert_unsupported_special_char(self, character):
                with pytest.raises(UnsupportedCharacterError,
                                   match=f"Unsupported character: {character}"):
                    editor_factory(f"Hello{character}World!")

            @pytest.mark.parametrize(
                "character_1",
                ["\a", "\b", "\f", "\r", "\v"]
            )
            @pytest.mark.parametrize(
                "character_2",
                ["\a", "\b", "\f", "\r", "\v"]
            )
            def test_insert_multiple_unsupported_special_char(self, character_1, character_2):
                with pytest.raises(UnsupportedCharacterError,
                                   match=f"Unsupported character: {character_1}|{character_2}"):
                    editor_factory(f"Hello{character_1}World!{character_2}")


class TestRemoveText:
    """Testing the delete and backspace methods."""

    class TestDelete:
        """Testing the delete method."""

        def test_delete_at_home(self):
            text = "Hello World!"
            editor, text = editor_factory(text, line_limit=100)

            editor.move_home()
            editor.delete()

            assert editor.text == text[1:]
            assert editor.get_lines() == [text[1:]]
            assert editor.get_sub_lines() == [[text[1:]]]

            # Cursor stays in place
            assert editor.cursor == (0, 0)
            assert editor.line_cursor == (0, 0)

        def test_delete_at_end(self):
            text = "Hello World!"
            editor, text = editor_factory(text, line_limit=100)

            editor.move_end()
            editor.delete()

            assert editor.text == text
            assert editor.get_lines() == [text]
            assert editor.get_sub_lines() == [[text]]

            assert editor.cursor == (0, len(text))
            assert editor.line_cursor == (0, len(text))

        def test_delete_end_of_display_line(self):
            text = "Hello World!"
            line_limit = len("Hello")

            editor, text = editor_factory(text, line_limit=line_limit, cursor=(0, line_limit))
            assert editor.cursor == (1, 0)

            editor.delete()

            assert editor.text == "HelloWorld!"
            assert editor.get_lines() == ["Hello", "World", "!"]
            assert editor.get_sub_lines() == [["Hello", "World", "!"]]

            assert editor.cursor == (1, 0)
            assert editor.line_cursor == (0, line_limit)

        def test_delete_end_of_logical_line(self):
            text = "Hello\nWorld!"

            editor, text = editor_factory(text, line_limit=100, cursor=(0, len("Hello")))
            assert editor.cursor == (0, 5)

            editor.delete()

            target_text = "HelloWorld!"
            assert editor.text == target_text
            assert editor.get_lines() == [target_text]
            assert editor.get_sub_lines() == [[target_text]]

            assert editor.cursor == (0, len("Hello"))
            assert editor.line_cursor == (0, len("Hello"))

    class TestBackspace:
        """Testing the backspace method."""

        def test_backspace_at_home(self):
            text = "Hello World!"
            editor, text = editor_factory(text, line_limit=100)

            editor.move_home()
            editor.backspace()

            assert editor.text == text
            assert editor.get_lines() == [text]
            assert editor.get_sub_lines() == [[text]]

            assert editor.cursor == (0, 0)
            assert editor.line_cursor == (0, 0)

        def test_backspace_end(self):
            text = "Hello World!"
            editor, text = editor_factory(text, line_limit=100)

            editor.move_end()
            editor.backspace()

            assert editor.text == text[:-1]
            assert editor.get_lines() == [text[:-1]]
            assert editor.get_sub_lines() == [[text[:-1]]]

            assert editor.cursor == (0, len(text) - 1)
            assert editor.line_cursor == (0, len(text) - 1)

        def test_backspace_start_of_display_line(self):
            text = "Hello World!"
            editor, text = editor_factory(text, line_limit=len("Hello"),
                                          cursor=(1, 0))  # cursor at start of display line

            editor.backspace()

            assert editor.text == "Hell World!"
            assert editor.get_lines() == ["Hell ", "World", "!"]
            assert editor.get_sub_lines() == [["Hell ", "World", "!"]]

            assert editor.cursor == (0, len("Hello") - 1)
            assert editor.line_cursor == (0, len("Hello") - 1)

        def test_backspace_start_of_logical_line(self):
            text = "Hello\nWorld!"
            editor, text = editor_factory(text, line_limit=100,
                                          cursor=(1, 0))  # cursor at start of logical line

            editor.backspace()

            target_text = "HelloWorld!"
            assert editor.text == target_text
            assert editor.get_lines() == [target_text]
            assert editor.get_sub_lines() == [[target_text]]

            assert editor.cursor == (0, len("Hello"))
            assert editor.line_cursor == (0, len("Hello"))
