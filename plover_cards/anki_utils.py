import aqt
from anki import Collection

ANKI_BASE_DIR = aqt.ProfileManager().base


def get_models(collection_path):
    collection = Collection(collection_path)
    return collection.models.all_names_and_ids()
