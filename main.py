import curses

from text_editor import TextEditor


def _movement_factory(editor: TextEditor):
    return {
        curses.KEY_LEFT: editor.move_left,
        curses.KEY_RIGHT: editor.move_right,
        curses.KEY_UP: editor.move_up,
        curses.KEY_DOWN: editor.move_down,
        curses.KEY_HOME: editor.move_home,
        curses.KEY_END: editor.move_end,
        curses.KEY_BACKSPACE: editor.backspace,
        8: editor.backspace,
        curses.KEY_DC: editor.delete,
    }


def _keystroke(stdscr, editor: TextEditor, movement_dict: dict):
    key = stdscr.getch()

    if key == 27:
        return True
    elif _move(key, movement_dict):
        return False
    else:
        try:
            editor.insert(chr(key))
        except ValueError:
            # Simply ignore invalid characters
            pass
        return False


def _move(key, movement_dict: dict):
    if key in movement_dict:
        movement_dict[key]()
        return True
    return False


def _display(stdscr, editor: TextEditor):
    line_c, col_c = editor.cursor
    total_lines = 0

    for line_nr, display_lines in enumerate(editor.get_logic_lines()):
        # Add line number
        line_indicator = f"{line_nr}: "
        stdscr.addstr(total_lines, 0, line_indicator)

        for display_line_nr, sub_line in enumerate(display_lines):
            is_cursor_line = (total_lines == line_c)

            if is_cursor_line:
                total_lines = _render_with_cursor(
                    stdscr, sub_line, col_c, len(line_indicator), total_lines, display_line_nr, len(display_lines),
                    editor.line_limit
                )
            else:
                stdscr.addstr(total_lines, len(line_indicator), sub_line)

            total_lines += 1

    stdscr.addstr(total_lines + 1, 0, f"Cursor: {editor.line_cursor}")


def _render_with_cursor(stdscr, sub_line, col_c, offset, total_lines, display_line_nr, line_len, line_limit):
    """
    Render a line with the cursor highlighted.
    """
    if col_c < len(sub_line):  # Cursor inside the line
        before, cursor, after = sub_line[:col_c], sub_line[col_c], sub_line[col_c + 1:]
        stdscr.addstr(total_lines, offset, before)
        stdscr.addstr(total_lines, offset + col_c, cursor, curses.A_REVERSE)
        stdscr.addstr(total_lines, offset + col_c + 1, after)

    elif col_c == line_limit:  # Cursor at line break
        stdscr.addstr(total_lines, offset, sub_line)
        stdscr.addstr(total_lines + 1, offset, "/", curses.A_REVERSE)
        if display_line_nr == line_len - 1:
            total_lines += 1

    else:  # Cursor after end of line (empty space)
        stdscr.addstr(total_lines, offset, sub_line)
        stdscr.addstr(total_lines, offset + len(sub_line), " ", curses.A_REVERSE)

    return total_lines


def _run_editor(stdscr, editor: TextEditor):
    curses.curs_set(0)  # hide terminal cursor
    stdscr.keypad(True)  # enable special keys
    stdscr.nodelay(True)  # prevent blocking

    movement_dict = _movement_factory(editor)

    try:
        while True:
            stdscr.clear()

            _display(stdscr, editor)

            stdscr.refresh()

            try:
                quit_flag = _keystroke(stdscr, editor, movement_dict)
                if quit_flag:
                    break
            except curses.error:
                # Ignore getch errors
                pass

    except KeyboardInterrupt:
        pass


def main():
    editor = TextEditor(line_limit=20, text="Welcome!")

    curses.wrapper(_run_editor, editor)


if __name__ == '__main__':
    main()
