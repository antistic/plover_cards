import csv
from dataclasses import dataclass, field
from pathlib import Path
import re

from plover_cards import anki_utils

NOTE_REPLACEMENTS = [
    ("&amp;", "&"),
    ("&gt;", ">"),
    ("&lt;", "<"),
]


def normalise_text(text):
    for find, replace in NOTE_REPLACEMENTS:
        text = text.replace(find, replace)
    return text.strip()


def get_existing_notes(query, compare_field):
    notes = anki_utils.get_notes(query)

    return set(normalise_text(note["fields"][compare_field]["value"]) for note in notes)


def get_ignored_from_file(ignore_file):
    if not ignore_file.exists():
        return set()
    return set(ignore_file.read_text().splitlines())


def get_new_notes(new_notes_file):
    if not new_notes_file.exists():
        return {}

    lines = new_notes_file.read_text().splitlines()
    reader = csv.reader(lines)
    result = {}
    for line in reader:
        if len(line) == 2:
            result[line[0]] = line[1]

    return result


@dataclass
class Card:
    translation: str
    stroke_suggestions: list[str]
    frequency: int
    frequency_shorter: int
    last_updated: int
    chosen_strokes: str = None
    ignored: bool = False
    similar_ignored: list[str] = field(default_factory=list)

    def choose_strokes(self, strokes):
        self.ignored = False
        self.chosen_strokes = strokes

    def ignore(self):
        self.ignored = True
        self.chosen_strokes = None

    def as_note(self):
        def escape(text):
            result = text.replace('"', '""')
            return f'"{result}"'

        return f"{escape(self.translation)},{escape(self.chosen_strokes)}"


def strokes_sort_key(strokes):
    num_strokes = strokes.count("/")
    return f"{num_strokes}{len(strokes)}{strokes}"


def similar_words(word):
    # does the reverse of tucked in suffix keys
    # https://github.com/openstenoproject/plover/blob/91a84e16403e9d7470d0192c3b5484e422060a0b/plover/system/english_stenotype.py#L32

    replacements = [
        ("s$", ""),
        ("es$", ""),
        ("ies$", "y"),
        ("ves$", "f"),
        ("ing$", ""),
        (r"(.)\1ing$", r"\1"),
        ("ing$", "e"),
        ("ying$", "ie"),
        ("ed$", ""),
        ("ied$", "y"),
        ("eed$", "ee"),
    ]

    words = set()
    for replacement in replacements:
        (similar_word, count) = re.subn(replacement[0], replacement[1], word)
        if count > 0:
            words.add(similar_word)

    words.add(word.lower())

    return words


def create_cards(card_suggestions, ignored, new_notes):
    suggestions = card_suggestions.card_suggestions

    cards = []
    num_ignored = 0
    for phrase, data in suggestions.copy().items():
        if phrase in ignored:
            num_ignored += 1
            card_suggestions.delete(phrase)
        else:
            card = Card(
                translation=phrase,
                stroke_suggestions=sorted(list(data["strokes"]), key=strokes_sort_key),
                frequency=data["frequency"],
                frequency_shorter=data.get("frequency_shorter", 0),
                last_updated=data.get("last_updated"),
                chosen_strokes=new_notes.get(phrase, None),
                similar_ignored=list(similar_words(phrase).intersection(ignored)),
            )
            cards.append(card)

    return (cards, num_ignored)


class Cards:
    def __init__(self, config, card_suggestions):
        self.config = config

        ignored = set()
        if self.config.getboolean("compare_ignore", "enabled"):
            self.ignored = get_ignored_from_file(
                Path(self.config["compare_ignore"]["file_path"])
            )
            ignored.update(self.ignored)
        if self.config.getboolean("compare_to_anki", "enabled"):
            ignored.update(
                get_existing_notes(
                    self.config["compare_to_anki"]["query"],
                    self.config["compare_to_anki"]["compare_field"],
                )
            )

        new_notes = {}
        if self.config.getboolean("output_csv", "enabled"):
            new_notes = get_new_notes(Path(self.config["output_csv"]["file_path"]))

        (self.cards, self.num_ignored) = create_cards(
            card_suggestions,
            ignored,
            new_notes,
        )

        self.new_ignored = set()
        self.num_saved = 0
        self.num_added = 0

    def __getitem__(self, index):
        return self.cards[index]

    def __len__(self):
        return len(self.cards)

    def choose_strokes(self, index, strokes):
        card = self.cards[index]
        card.choose_strokes(strokes)
        self.new_ignored.discard(card.translation)

    def ignore(self, index):
        card = self.cards[index]
        card.ignore()
        self.new_ignored.add(card.translation)

    def save(self):
        notes = []

        if self.config.getboolean("output_csv", "enabled"):
            output_path = Path(self.config["output_csv"]["file_path"])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            notes = self._as_notes()
            self.num_saved = len(notes)

            mode = (
                "w" if self.config["output_csv"]["write_method"] == "Overwrite" else "a"
            )
            with output_path.open(mode) as f:
                f.write("\n".join(notes))
                f.write("\n")

        if self.config.getboolean("add_to_anki", "enabled"):
            anki_settings = self.config["add_to_anki"]
            added = anki_utils.invoke(
                "addNotes",
                notes=[
                    {
                        "deckName": anki_settings["deck"],
                        "modelName": anki_settings["note_type"],
                        "fields": {
                            anki_settings["translation_field"]: card.translation,
                            anki_settings["strokes_field"]: card.chosen_strokes,
                        },
                        "tags": anki_settings["tags"].split(" "),
                        "options": {
                            # Duplicates shouldn't be showing up, but in case they do,
                            # I don't want this to blow up
                            "allowDuplicate": True
                        },
                    }
                    for card in self.cards
                    if not card.ignored and card.chosen_strokes
                ],
            )

            self.num_added = sum(1 for note in added if note != "null")

        if self.config.getboolean("compare_ignore", "enabled"):
            ignore_path = Path(self.config["compare_ignore"]["file_path"])
            all_ignored = self.ignored.union(self.new_ignored)
            ignore_path.parent.mkdir(parents=True, exist_ok=True)
            ignore_path.write_text("\n".join(sorted(list(all_ignored))))

    def sort(self, *args, **kwargs):
        self.cards.sort(*args, **kwargs)

    def _as_notes(self):
        return [
            card.as_note()
            for card in self.cards
            if not card.ignored and card.chosen_strokes
        ]
