import re

from plover.formatting import RetroFormatter

from .card_suggestions import CardSuggestions


def tails(ls):
    """Return all tail combinations
    tails :: [x] -> [[x]]
    >>> tails('abcd')
    ['abcd', 'bcd', 'cd', d']

    https://github.com/openstenoproject/plover/blob/91a84e16403e9d7470d0192c3b5484e422060a0b/plover/gui_qt/suggestions_dialog.py#L106
    """

    for i in range(len(ls)):
        yield ls[i:]


class Main:

    WORD_RX = re.compile(r"(?:\w+|[^\w\s]+)\s*")

    def __init__(self, engine):
        super().__init__()
        self.engine = engine

        self.card_suggestions = CardSuggestions()

    def start(self):
        self.engine.hook_connect("translated", self._on_translated)
        self.engine._translator.add_listener(self._on_translator_output)

    def stop(self):
        self.engine.hook_disconnect("translated", self._on_translated)
        self.card_suggestions.save()

    def _on_translated(self, _old, new):
        """https://github.com/openstenoproject/plover/blob/91a84e16403e9d7470d0192c3b5484e422060a0b/plover/gui_qt/suggestions_dialog.py#L118"""

        for action in reversed(new):
            if action.text and not action.text.isspace():
                break
        else:
            return

        with self.engine:
            last_translations = self.engine.translator_state.translations
            retro_formatter = RetroFormatter(last_translations)
            split_words = retro_formatter.last_words(10, rx=self.WORD_RX)

        for phrase in tails(split_words):
            phrase = "".join(phrase)
            for suggestion in self.engine.get_suggestions(phrase):
                self.card_suggestions.add_suggestion(suggestion)

    def _on_translator_output(self, _undo, do, _prev):
        for translation in do:
            self.card_suggestions.add_translation(translation)
