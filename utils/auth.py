import base64
import json

def base64_to_json(base64_str, output_path):
    json_str = base64.b64decode(base64_str).decode()
    data = json.loads(json_str)
    with open(output_path, 'w') as f:
        json.dump(data, f)


def json_to_base64(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    json_str = json.dumps(data)
    return base64.b64encode(json_str.encode()).decode()


def string_to_json(json_str, output_path):
    data = json.loads(json_str)
    with open(output_path, 'w') as f:
        json.dump(data, f)


def json_to_string(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return json.dumps(data)