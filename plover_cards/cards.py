import sqlite3

import csv
from dataclasses import dataclass, field
from pathlib import Path
import re


def get_existing_notes(anki_path, card_type):
    conn = sqlite3.connect(f"file:{anki_path}?mode=ro", uri=True)
    with conn:
        cursor = conn.cursor()
        cursor.execute("select sfld from notes where mid=?;", [card_type])
        results = cursor.fetchall()

    return set(map(lambda r: r[0], results))


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
        result[line[0]] = line[1]

    return result


def get_suggestions_from_strokes_log(strokes_path, suggestions, ignored):
    strokes_pattern = re.compile(r".* Translation\(\((.*)\) : \"(.*)\"\)")
    ignore_endings = ["s", "ed", "ing"]
    word_ignore_patterns = [
        re.compile(rf" {{\^{ending}}}$") for ending in ignore_endings
    ]
    word_ignore_patterns.append(re.compile(r"\{\^\~\|\^\}"))  # retroactively add space

    def parse_stroke(s):
        match = strokes_pattern.match(s)

        if match:
            word = match.group(2).strip()
            for pattern in word_ignore_patterns:
                if pattern.search(word):
                    return None

            strokes = match.group(1).replace("'", "")
            # remove trailing comma
            strokes = re.sub(r",$", "", strokes)
            strokes = strokes.split(", ")
            strokes = ["/".join(strokes)]

            return (word, strokes)
        return None

    strokes = strokes_path.read_text().splitlines()
    for line in strokes:
        result = parse_stroke(line)
        if result:
            (word, strokes) = result
            if word and word not in ignored:
                if word in suggestions:
                    suggestions[word] = suggestions[word].union(strokes)
                else:
                    suggestions[word] = set(strokes)

    return suggestions


def add_improvements_from_clippy(clippy_path, suggestions, ignored):
    shorter_stroke_pattern = re.compile(r"\[.*\] (.*)\|\|.*-> (.*)")

    def parse_shorter_stroke(s):
        match = shorter_stroke_pattern.match(s)
        if match:
            return (
                match.group(1).strip(),
                match.group(2).split(", "),
            )

    # add improvements
    shorter_strokes = clippy_path.read_text().splitlines()
    for line in shorter_strokes:
        result = parse_shorter_stroke(line)
        if result:
            (word, strokes) = result
            if word and word not in ignored:
                if word in suggestions:
                    suggestions[word] = suggestions[word].union(strokes)
                elif len(word.split(" ")) > 1:
                    # only add improvements for unknown phrases, not unknown words
                    suggestions[word] = set(strokes)

    return suggestions


@dataclass
class Card:
    translation: str
    stroke_suggestions: list[str]
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


def possible_roots(word):
    replacements = [
        ("s$", ""),
        ("es$", ""),
        ("ies$", "y"),
        ("ves$", "f"),
        ("ing$", ""),
        (".ing$", ""),
        ("ing$", "e"),
        ("ying$", "ie"),
        ("d$", ""),
        ("ed$", ""),
        ("ied$", "y"),
        ("eed$", "ee"),
    ]

    possible_roots = set()
    for replacement in replacements:
        (root, count) = re.subn(replacement[0], replacement[1], word)
        if count > 0:
            possible_roots.add(root)

    possible_roots.add(word.lower())

    return possible_roots


def create_suggestions(strokes_path, clippy_path, ignored, new_notes):
    suggestions = {}
    suggestions = get_suggestions_from_strokes_log(strokes_path, suggestions, ignored)
    suggestions = add_improvements_from_clippy(clippy_path, suggestions, ignored)

    suggestions = [
        Card(
            translation=k,
            stroke_suggestions=sorted(list(v), key=strokes_sort_key),
            chosen_strokes=new_notes.get(k, None),
            similar_ignored=list(possible_roots(k).intersection(ignored)),
        )
        for k, v in sorted(suggestions.items(), key=lambda x: x[0].lower())
    ]

    return suggestions


class Cards:
    def __init__(
        self,
        anki_path,
        card_type,
        clippy_path,
        strokes_path,
        ignore_path,
        output_path,
    ):
        self.clippy_path = Path(clippy_path)
        self.strokes_path = Path(strokes_path)
        self.ignore_path = Path(ignore_path)
        self.output_path = Path(output_path)

        existing_notes = get_existing_notes(anki_path, card_type)
        self.ignored = get_ignored_from_file(self.ignore_path)

        new_notes = get_new_notes(self.output_path)
        self.cards = create_suggestions(
            Path(strokes_path),
            Path(clippy_path),
            existing_notes.union(self.ignored),
            new_notes,
        )

        self.new_ignored = set()

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
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("a") as f:
            f.write(self._as_notes())
            f.write("\n")

        all_ignored = self.ignored.union(self.new_ignored)
        self.ignore_path.parent.mkdir(parents=True, exist_ok=True)
        self.ignore_path.write_text("\n".join(sorted(list(all_ignored))))

    def clear_strokes(self):
        self.strokes_path.write_text("")

    def clear_clippy(self):
        self.clippy_path.write_text("")

    def _as_notes(self):
        return "\n".join(
            [
                card.as_note()
                for card in self.cards
                if not card.ignored and card.chosen_strokes
            ]
        )
