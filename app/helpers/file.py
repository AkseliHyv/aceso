import json, os

def load_file(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return None

def save_file(path, data):
    with open(path, "w") as f:
        json.dump(data, f)