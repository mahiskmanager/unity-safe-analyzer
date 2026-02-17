import re
from ..config import MAX_STRING_RESULTS

def scan_strings(file_path, min_length=6):
    results = []

    with open(file_path, "rb") as f:
        data = f.read()

    pattern = re.compile(rb"[ -~]{%d,}" % min_length)
    matches = pattern.findall(data)

    for m in matches:
        try:
            results.append(m.decode("utf-8"))
        except UnicodeDecodeError:
            continue

        if len(results) >= MAX_STRING_RESULTS:
            break

    return results
