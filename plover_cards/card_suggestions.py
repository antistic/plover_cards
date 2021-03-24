from pathlib import Path
import pickle
from threading import Lock

from plover.oslayer.config import CONFIG_DIR as PLOVER_CONFIG_DIR


def sync(func):
    def f(self, *args, **kwargs):
        with self.lock:
            return func(self, *args, **kwargs)

    return f


class CardSuggestions:
    PATH = Path(PLOVER_CONFIG_DIR, "plover_cards", "card_suggestions.pickle")
    lock = Lock()

    def __init__(self):
        self.load()
        self.changed = False

    @sync
    def load(self):
        self.card_suggestions = {}
        if self.PATH.exists():
            with self.PATH.open("rb") as f:
                self.card_suggestions = pickle.load(f)

    @sync
    def save(self):
        if not self.changed:
            return

        with self.PATH.open("wb") as f:
            pickle.dump(self.card_suggestions, f)

        self.changed = False

    @sync
    def add_suggestion(self, suggestion):
        text = suggestion.text
        stroke_suggestions = ["/".join(s) for s in suggestion.steno_list]

        if self.card_suggestions.get(text) is None:
            self.card_suggestions[text] = {
                "frequency": 0,
                "strokes": set(),
            }

        self.card_suggestions[text]["frequency"] += 1
        self.card_suggestions[text]["strokes"].update(stroke_suggestions)

        self.changed = True

    @sync
    def delete(self, text):
        del self.card_suggestions[text]
