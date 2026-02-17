import os
import json

def generate_json_report(results, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "report.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    return path

