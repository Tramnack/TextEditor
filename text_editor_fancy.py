from textwrap import wrap

from text_editor import TextEditor


class TextEditorFancy(TextEditor):
    """Variant of TextEditor that avoids splitting words."""

    def _wrap_lines(self):
        lines = []
        for raw_line in self._text.split("\n"):
            lines.append(wrap(raw_line, self._line_limit,
                              break_on_hyphens=True,
                              break_long_words=True,
                              replace_whitespace=False,
                              drop_whitespace=False,
                              expand_tabs=False))
        lines = [
            line or [""] for line in lines
        ]
        self._logic_lines = lines

        self._display_lines = [
            c
            for sub_line in self._logic_lines
            for c in sub_line
        ]
