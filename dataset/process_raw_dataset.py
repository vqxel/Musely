import json
import argparse
from pathlib import Path
from typing import Any
from collections import defaultdict
from collections import Counter 
import math
from dataset_loader import load_filepaths_from_dir, load_dataset
import logging

logging.basicConfig(
  level=logging.DEBUG,
  format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

def extract_keys(obj):
    playlists = obj["playlists"]
    return [playlist["pid"] for playlist in playlists]

def extract_values(obj):
    popped_playlists = obj["playlists"]
    playlists_tracks = [playlist["tracks"] for playlist in popped_playlists]
    playlists_tracks_sets = []
    for playlist_tracks in playlists_tracks:
        track_set = set()
        for track in playlist_tracks:
            track_set.add(track["track_uri"].replace("spotify:track:", ""))
        playlists_tracks_sets.append(track_set)
    return playlists_tracks_sets


def clean_raw_dataset_json(obj):
    playlists = obj.pop("playlists")
    for playlist in playlists:
        # Remove extra playlist metadata
        del playlist["collaborative"]
        del playlist["modified_at"]
        del playlist["num_tracks"]
        del playlist["num_albums"]
        del playlist["num_followers"]
        del playlist["num_edits"]
        del playlist["duration_ms"]
        del playlist["num_artists"]

        # Remove extra track metadata
        for j, track in enumerate(playlist["tracks"]):
            playlist["tracks"][j] = track["track_uri"].replace("spotify:track:", "")
    return playlists 

def chunk_generated_cleaned_dataset(dataset, chunk_count: int):
    if not dataset:
        return []
    chunk_size = math.ceil(len(dataset) / chunk_count)
    chunks = [dataset[i:i+chunk_size] for i in range(0, len(dataset), chunk_size)]
    return chunks

def chunk_dict(dataset, chunk_count: int):
    items = list(dataset.items())
    if not items:
        return []
    chunk_size = math.ceil(len(items) / chunk_count)
    chunks = [
        dict(items[i:i+chunk_size])
        for i in range(0, len(items), chunk_size)
    ]
    return chunks
    
def generate_songs_to_playlists_dataset(dataset):
    inverted_dataset = defaultdict(list)
    for playlist_id in dataset:
        if playlist_id % 1000 == 0:
            logging.debug(f"Reading through playlist {playlist_id}")
        for track in dataset[playlist_id]:
            inverted_dataset[track].append(playlist_id)
    return inverted_dataset

def main():
    parser = argparse.ArgumentParser(description="A script meant to locally generate a complementary dataset based on the Spotify 1 million playlist dataset that maps songs to the playlists they're included in.")

    parser.add_argument("-rd", "--raw_dataset", type=Path, default=Path("./"), help="The path the original dataset resides in.")

    parser.add_argument("-cd", "--clean_dataset", type=Path, default=None, help="The path the cleaned version of the original dataset resides in.")

    parser.add_argument("-c", "--cleaned_raw_out", type=Path, default=None, help="The path to output the intermediate cleaned raw dataset into.")

    parser.add_argument("-o", "--output", type=Path, default=Path("./"), help="The output path for the complementary dataset.")

    args = parser.parse_args()


    # Parse input dataset
    using_raw_dataset = True
    dataset_path = args.raw_dataset
    if args.clean_dataset is not None:
        using_raw_dataset = False
        dataset_path = args.clean_dataset

    filepaths = load_filepaths_from_dir(dataset_path)
    files = load_dataset(filepaths, extract_key=extract_keys, extract_value=extract_values)

    class SetEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, set):
                return list(o)
            return super().default(o)

    # Chunk and save data if using a raw dataset
    if using_raw_dataset and args.cleaned_raw_out is not None:
        chunks = chunk_dict(files, 1000)
        for i, chunk in enumerate(chunks):
            with open(args.cleaned_raw_out / f"playlists_{i}.json", "w") as f:
                json.dump(chunk, f, indent=4, cls=SetEncoder)


    # Invert dataset
    inverted_dataset = generate_songs_to_playlists_dataset(files)

    chunks = chunk_dict(inverted_dataset, 1000)
    for i, chunk in enumerate(chunks):
        with open(args.output / f"songs_{i}.json", "w") as f:
            json.dump(chunk, f, indent=4, cls=SetEncoder)

    
if __name__ == "__main__":
    main()
