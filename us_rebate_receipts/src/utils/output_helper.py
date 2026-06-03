from datetime import datetime
from pathlib import Path
from utils.path_helper import get_output_dir

def get_next_batch_dir() -> Path:
    output_dir = get_output_dir()
    today = datetime.now().strftime("%Y-%m-%d")

    existing = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith(today)]
    batch_num = len(existing) + 1

    batch_dir = output_dir / f"{today}_batch_{batch_num:03d}"
    batch_dir.mkdir(parents=True, exist_ok=True)
    return batch_dir
