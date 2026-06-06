from dataset_loader import load_filepaths_from_dir, load_clean_dataset
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
import argparse
from pathlib import Path
import logging
from collections import deque
from collections import Counter 
import numpy as np
from scipy.sparse import coo_matrix, csr_matrix, save_npz, load_npz
import json

logging.basicConfig(
  level=logging.DEBUG,
  format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

def get_song_idx_dicts(songs):
    song_to_idx = {
        song_id : i for i, song_id in enumerate(songs)
    }

    idx_to_song = {
        i : song_id for song_id, i in song_to_idx.items() 
    }

    return (song_to_idx, idx_to_song)

def gen_sparse_mat(song_to_idx, sts):
    rows = []
    cols = []
    weights = []
    for song_a, song_b, weight in sts:
        rows.append(song_to_idx[song_a])
        cols.append(song_to_idx[song_b])
        weights.append(weight)

    graph_mat = coo_matrix(
        (weights, (rows, cols)),
        shape=(len(song_to_idx), len(song_to_idx)),
        dtype=np.int32 # Consider float32
    ).tocsr()

    graph_mat = graph_mat.maximum(graph_mat.T) 

    return graph_mat

def get_top_connected_songs(graph_mat, idx_to_song, limit: int = 25):
    connection_counts = graph_mat.getnnz(axis=1)

    top_indices = connection_counts.argsort()[::-1][:limit]

    return [
      {
          "song_id": idx_to_song[int(idx)],
          "matrix_idx": int(idx),
          "connection_count": int(connection_counts[idx]),
      }
      for idx in top_indices
  ]

def main():
    parser = argparse.ArgumentParser(description="A script meant to take both input datasets and generate a graph.")

    parser.add_argument("songs_to_playlists", type=Path, help="The path the songs to playlists dataset resides in.")

    parser.add_argument("playlists_to_songs", type=Path, help="The path the playlists to songs dataset resides in.")

    parser.add_argument("mat_save_dir", type=Path, help="The path the output graph gets stored in.")

    args = parser.parse_args()

    stp_filepaths = load_filepaths_from_dir(args.songs_to_playlists)
    pts_filepaths = load_filepaths_from_dir(args.playlists_to_songs)
    stp_dataset = load_clean_dataset(stp_filepaths)
    pts_dataset = load_clean_dataset(pts_filepaths)

    queue = deque()
    root_songs = set()
    sts = []

    first_song = next(iter(stp_dataset.keys()))
    queue.append(first_song)

    G = nx.Graph()

    while queue:
        song_id = queue.popleft()

        # Ensure that this song hasn't already been searched from
        if song_id not in root_songs:
            connected_songs = []

            playlists = stp_dataset[song_id]
            for playlist in playlists:
                connected_songs_in_playlist = pts_dataset[str(playlist)]
                # Ensure no double counting
                connected_songs_in_playlist -= root_songs
                connected_songs += list(connected_songs_in_playlist)

            connection_counter = Counter(connected_songs)
            connection_counter.pop(song_id, None)

            for connection in connection_counter.items():
                connection_id = connection[0]
                connection_count = connection[1]
                queue.append(connection_id)
                sts.append((song_id, connection_id, connection_count))

            root_songs.add(song_id)
            logging.debug(f"{song_id} in {len(playlists)} playlists. Connected to {connection_counter.total()} songs")
    
    song_to_idx, idx_to_song = get_song_idx_dicts(stp_dataset.keys())
    graph_mat = gen_sparse_mat(song_to_idx, sts)

    top_connected_songs = get_top_connected_songs(graph_mat, idx_to_song, limit=100)

    save_npz(args.mat_save_dir / "graph_mat.npz", graph_mat)

    with open(args.mat_save_dir / "top_connected_songs.json", "w") as f:
        json.dump(top_connected_songs, f, indent=4)

    with open(args.mat_save_dir / "song_to_idx.json", "w") as f:
        json.dump(song_to_idx, f, indent=4)

    with open(args.mat_save_dir / "idx_to_song.json", "w") as f:
        json.dump(idx_to_song, f, indent=4)

if __name__ == "__main__":
    main()
