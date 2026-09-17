"""Small shared utilities.

atomic_write_json writes to a temp file then renames it into place, so a
crash or interrupt mid-write can't leave a half-written, corrupted JSON
file behind (os.replace is atomic on the same filesystem).
"""

import json
import os


def atomic_write_json(path: str, data) -> None:
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)
