import json
import logging
from pathlib import Path
from typing import Any
from collections.abc import Callable

logger = logging.getLogger(__name__)

def load_filepaths_from_dir(dir: Path) -> list[Path]:
    abs_paths = [p.resolve() for p in dir.rglob("*.json") if p.is_file()]
    return abs_paths

def load_dataset(filepaths: list[Path], extract_key: Callable[[Any], list[Any]], extract_value: Callable[[Any], list[Any]]):
    dataset = {}
    for i, path in enumerate(filepaths):
        with open(path, "r") as file:
            extracted_data = json.load(file)

            keys = extract_key(extracted_data)
            values = extract_value(extracted_data)
            
            dataset |= dict(zip(keys, values)) 
            logger.debug(f"Finished injesting {path} ({i+1}/{len(filepaths)})")
    return dataset 

def load_clean_dataset(filepaths: list[Path]):
    dataset = {}
    for i, path in enumerate(filepaths):
        with open(path, "r") as file:
            extracted_data = json.load(file)

            set_data = {k: set(v) for k, v in extracted_data.items()}

            dataset |= set_data
            logger.debug(f"Finished injesting {path} ({i+1}/{len(filepaths)})")
    return dataset 
