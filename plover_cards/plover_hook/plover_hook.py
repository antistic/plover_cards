import re
from threading import Timer

from plover.formatting import RetroFormatter
from plover.translation import escape_translation

from .card_suggestions import CardSuggestions

# same as in suggestions dialog and plover_clippy
MAX_PHRASE_PARTS = 10
# it's unlikely you'll have more than 5 translations per word for 10 words
MAX_TRANSLATIONS = 50
# misstrokes are often only a key or two different
MISSTROKE_OFFSET = 3

# 5 minutes
SAVE_INTERVAL = 300


class Main:

    # from suggestions dialog
    # https://github.com/openstenoproject/plover/blob/91a84e16403e9d7470d0192c3b5484e422060a0b/plover/gui_qt/suggestions_dialog.py#L36
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

        self.timer = Timer(SAVE_INTERVAL, self._on_timer)
        self.timer.start()

    def _on_translated(self, _old, new):
        if len(new) == 0:
            # true if the stroke is an undo stroke
            return

        with self.engine:
            last_translations = self.engine.translator_state.translations[
                -MAX_TRANSLATIONS:
            ]

        if len(last_translations) == 0:
            return

        phrases = set()
        # last translation in case it isn't shown exactly, e.g. "{#Return}{^}", {^ing}
        last_translation = last_translations[-1].english
        if last_translation is not None:
            phrases.add(escape_translation(last_translation))

        last_translations = [
            translation
            for translation in last_translations
            # strip out any command/combo translations since they don't make sense as
            # part of phrases
            if any(
                action.command is None and action.combo is None
                for action in translation.formatting
            )
        ]
        retro_formatter = RetroFormatter(last_translations)
        split_words = retro_formatter.last_words(MAX_PHRASE_PARTS, rx=self.WORD_RX)

        # last few "phrases", e.g. "let's go", "'s go", "s go", "go"
        phrases.update(set("".join(split_words[i:]) for i in range(len(split_words))))

        # build up a dictionary of phrase -> stroke from translations
        # these phrases are a subset of what's in phrases, since it's only the phrases
        # you actually wrote
        #   e.g. if you wrote "let's go"
        #     phrases: {"let's go", "'s go", "s go", "go"}
        #     phrase_strokes: {"let's go": ("HRETS", "TKPWO"), "go": ("TKPWO",)}
        phrase_strokes = {}
        previous = ""
        for i in range(len(last_translations)):
            translations = last_translations[i:]
            phrase = "".join(
                RetroFormatter(translations).last_words(
                    MAX_PHRASE_PARTS, rx=self.WORD_RX
                )
            )

            if phrase == previous:
                continue
            previous = phrase

            strokes = tuple(
                part for translation in translations for part in translation.rtfcre
            )

            phrase_strokes[phrase] = strokes

        for phrase in phrases:
            strokes = phrase_strokes.get(phrase, "")
            with self.engine:
                suggestions = self.engine.get_suggestions(phrase)
            for suggestion in suggestions:
                self.card_suggestions.add_suggestion(
                    suggestion,
                    # is shorter if
                    any(
                        # there are fewer overall strokes
                        (len(s) < len(strokes))
                        or (
                            # there is one stroke which is at least MISSTROKE_OFFSET
                            # characters shorter
                            len(s) == 0
                            and len(s[0]) + MISSTROKE_OFFSET <= len(strokes[0])
                        )
                        for s in suggestion.steno_list
                    ),
                )
