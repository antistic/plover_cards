import configparser
from pathlib import Path

from plover.oslayer.config import CONFIG_DIR as PLOVER_CONFIG_DIR
from plover_cards import anki_utils

CONFIG_PATH = Path(PLOVER_CONFIG_DIR, "plover_cards.cfg")


def migrate(config):
    if config.has_section("paths"):
        if config.has_option("paths", "anki_collection"):
            # anki connect uses the active collection
            del config["paths"]["anki_collection"]

        if config.has_option("paths", "ignore"):
            config["compare_ignore"]["enabled"] = "yes"
            config["compare_ignore"]["file_path"] = config["paths"]["ignore"]
            del config["paths"]["ignore"]

        if config.has_option("paths", "output"):
            config["output_csv"]["enabled"] = "yes"
            config["output_csv"]["file_path"] = config["paths"]["output"]
            del config["paths"]["output"]

        del config["paths"]

    if config.has_section("anki"):
        note_type = ""

        if config.has_option("anki", "card_type"):
            note_type = config["anki"]["card_type"]
            del config["anki"]["card_type"]

        if config.has_option("anki", "note_type"):
            note_type = config["anki"]["note_type"]
            del config["anki"]["note_type"]

        if note_type in anki_utils.invoke("modelNames"):
            config["compare_to_anki"]["enabled"] = "yes"
            config["compare_to_anki"]["query"] = f"note:{note_type}"
            config["compare_to_anki"]["compare_field"] = anki_utils.invoke(
                "modelFieldNames", modelName=note_type
            )[0]

            config["add_to_anki"]["enabled"] = "yes"
            config["add_to_anki"]["note_type"] = note_type

        del config["anki"]

    if config.has_section("options"):
        if config.has_option("options", "clear_output_on_start"):
            if config["options"]["clear_output_on_start"] == "True":
                config["output_csv"]["enabled"] = "yes"
                config["output_csv"]["write_method"] = "Overwrite"
            else:
                config["output_csv"]["write_method"] = "Append"

            del config["options"]["clear_output_on_start"]

        if config.has_option("options", "clear_clippy"):
            # plover_cards no longer relies on clippy output
            del config["options"]["clear_clippy"]

        if config.has_option("options", "clear_strokes"):
            # plover_cards no longer relies on strokes log output
            del config["options"]["clear_strokes"]

        del config["options"]


def reset(config):
    config["compare_ignore"] = {
        "enabled": "yes",
        "file_path": str(Path(PLOVER_CONFIG_DIR, "plover_cards", "ignore.txt")),
    }

    config["compare_to_anki"] = {
        "enabled": "no",
        "query": "note:Basic",
        "compare_field": "Front",
    }

    config["output_csv"] = {
        "enabled": "no",
        "file_path": "",
        "write_method": "Overwrite",
    }

    config["add_to_anki"] = {
        "enabled": "no",
        "deck": "",
        "note_type": "",
        "translation_field": "",
        "strokes_field": "",
        "tags": "",
    }


def read():
    config = configparser.ConfigParser()
    reset(config)

    if not CONFIG_PATH.exists():
        save(config)
    else:
        config.read(str(CONFIG_PATH))
        migrate(config)
        save(config)

    return config


def save(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w") as config_file:
        config.write(config_file)
