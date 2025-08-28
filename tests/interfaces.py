from abc import abstractmethod


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
