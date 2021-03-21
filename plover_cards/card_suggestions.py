from pathlib import Path
import pickle
import re

from plover.oslayer.config import CONFIG_DIR as PLOVER_CONFIG_DIR
from plover.translation import escape_translation
from plover.orthography import add_suffix

SUFFIX_PATTERN = re.compile(r"^(.+) {\^(.+)}$")


def apply_suffix(text):
    match = SUFFIX_PATTERN.match(text)

    if match:
        print("match", match)
        return add_suffix(match.group(1), match.group(2))

    return text


class CardSuggestions:
    PATH = Path(PLOVER_CONFIG_DIR, "plover_cards", "card_suggestions.pickle")

    def __init__(self):
        self.load()

    def load(self):
        self.card_suggestions = {}
        if self.PATH.exists():
            with self.PATH.open("rb") as f:
                self.card_suggestions = pickle.load(f)

    def save(self):
        with self.PATH.open("wb") as f:
            pickle.dump(self.card_suggestions, f)

    def add(self, text, stroke_suggestions):
        if text is None:
            return

        if self.card_suggestions.get(text) is None:
            self.card_suggestions[text] = {
                "frequency": 0,
                "strokes": set(),
            }

        self.card_suggestions[text]["frequency"] += 1
        self.card_suggestions[text]["strokes"].update(stroke_suggestions)

    def add_suggestion(self, suggestion):
        stroke_suggestions = ["/".join(s) for s in suggestion.steno_list]
        self.add(suggestion.text, stroke_suggestions)

    def add_translation(self, translation):
        if translation.english is None:
            return

        text = escape_translation(translation.english)
        text = apply_suffix(text)
        self.add(text, ["/".join(translation.rtfcre)])

    def delete(self, text):
        del self.card_suggestions[text]
