import configparser
from pathlib import Path

from plover.oslayer.config import CONFIG_DIR as PLOVER_CONFIG_DIR
from .anki_utils import ANKI_BASE_DIR

CONFIG_PATH = Path(PLOVER_CONFIG_DIR, "plover_cards.cfg")


def read_config():
    config = configparser.ConfigParser()

    config["paths"] = {
        "ignore": str(Path(PLOVER_CONFIG_DIR, "plover_cards", "ignore.txt")),
        "output": str(Path(PLOVER_CONFIG_DIR, "plover_cards", "new_notes.txt")),
    }
    collections = list(Path(ANKI_BASE_DIR).glob("*/*.anki2"))
    if len(collections) > 0:
        config["paths"]["anki_collection"] = str(collections[0])

    config["anki"] = {"note_type": "Basic"}

    config["options"] = {
        "clear_output_on_start": "False",
    }

    if not CONFIG_PATH.exists():
        save_config(config)
    else:
        config.read(str(CONFIG_PATH))
    return config


def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w") as config_file:
        config.write(config_file)
