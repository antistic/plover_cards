from plover.formatting import RetroFormatter

from plover_cards import anki_utils
from plover_cards import config

CONFIG = config.read()


def add_card(engine, args):
    if args:
        num_words = int(args)
    else:
        num_words = 1

    with engine:
        last_translations = engine.translator_state.translations
        retro_formatter = RetroFormatter(last_translations)
        text = " ".join(retro_formatter.last_words(count=num_words, strip=True))
        strokes = "<br>\n".join(
            "<br>\n".join("/".join(s) for s in suggestion.steno_list)
            for suggestion in engine.get_suggestions(text)
        )

    anki_utils.invoke(
        "guiAddCards",
        note={
            "deckName": CONFIG.get("add_to_anki", "deck"),
            "modelName": CONFIG.get("add_to_anki", "note_type"),
            "fields": {
                CONFIG.get("add_to_anki", "translation_field"): text,
                CONFIG.get("add_to_anki", "strokes_field"): strokes,
            },
            "options": {
                "closeAfterAdding": True,
            },
            "tags": CONFIG.get("add_to_anki", "tags"),
        },
    )
