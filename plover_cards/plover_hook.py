import re
from threading import Timer

from plover.formatting import RetroFormatter
from plover.translation import escape_translation

from .card_suggestions import CardSuggestions


class Main:

    # from https://github.com/openstenoproject/plover/blob/91a84e16403e9d7470d0192c3b5484e422060a0b/plover/gui_qt/suggestions_dialog.py#L36
    WORD_RX = re.compile(r"(?:\w+|[^\w\s]+)\s*")

    def __init__(self, engine):
        super().__init__()
        self.engine = engine

        self.card_suggestions = CardSuggestions()
        self._on_timer()

    def start(self):
        self.engine.hook_connect("translated", self._on_translated)

    def stop(self):
        self.engine.hook_disconnect("translated", self._on_translated)
        self.card_suggestions.save()
        self.timer.cancel()

    def _on_timer(self):
        self.card_suggestions.save()

        self.timer = Timer(300, self._on_timer)
        self.timer.start()

    def _on_translated(self, _old, new):
        if len(new) == 0:
            # true if the stroke is an undo stroke
            return

        with self.engine:
            last_translations = self.engine.translator_state.translations
            retro_formatter = RetroFormatter(last_translations)
            split_words = retro_formatter.last_words(10, rx=self.WORD_RX)

        # last few "phrases", e.g. "let's go", "'s go", "s go", "go"
        phrases = set(("".join(split_words[i:]) for i in range(len(split_words))))
        # last translation in case it isn't shown exactly, e.g. "{#Return}{^}", {^ing}
        if len(last_translations) > 0:
            last_translation = last_translations[-1].english
            if last_translation is not None:
                phrases.add(escape_translation(last_translation))

        for phrase in phrases:
            for suggestion in self.engine.get_suggestions(phrase):
                self.card_suggestions.add_suggestion(suggestion)
