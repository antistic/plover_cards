import json
import urllib.request


def request(action, **params):
    return {"action": action, "params": params, "version": 6}


def invoke(action, **params):
    request_json = json.dumps(request(action, **params)).encode("utf-8")
    response = json.load(
        urllib.request.urlopen(
            urllib.request.Request("http://localhost:8765", request_json)
        )
    )
    if len(response) != 2:
        raise Exception("response has an unexpected number of fields")
    if "error" not in response:
        raise Exception("response is missing required error field")
    if "result" not in response:
        raise Exception("response is missing required result field")
    if response["error"] is not None:
        raise Exception(response["error"])
    return response["result"]


def get_notes(query):
    note_ids = invoke("findNotes", query=query)
    notes = invoke("notesInfo", notes=note_ids)

    return notes


def all_field_names():
    models = invoke("modelNames")

    fields = set()
    for model in models:
        fields.update(set(invoke("modelFieldNames", modelName=model)))

    return sorted(list(fields))
