from dataset_loader import load_filepaths_from_dir, load_clean_dataset
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
import argparse
from pathlib import Path
import logging
from collections import deque
from collections import Counter 

logging.basicConfig(
  level=logging.DEBUG,
  format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

def main():
    parser = argparse.ArgumentParser(description="A script meant to take both input datasets and generate a graph.")

    parser.add_argument("songs_to_playlists", type=Path, help="The path the songs to playlists dataset resides in.")

    parser.add_argument("playlists_to_songs", type=Path, help="The path the playlists to songs dataset resides in.")

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
                connected_songs += connected_songs_in_playlist

            connection_counter = Counter(connected_songs)
            connection_counter.pop(song_id, None)

            for connection in connection_counter.items():
                connection_id = connection[0]
                connection_count = connection[1]
                queue.append(connection_id)
                sts.append((song_id, connection_id, connection_count))

            root_songs.add(song_id)
            logging.debug(f"{song_id} in {len(playlists)} playlists. Connected to {connection_counter.total()} songs")
    
    logging.debug("Done creating graph")
    G.add_weighted_edges_from((a, b, w) for a, b, w in sts[:50_000] if w >= 3)
    logging.debug("Done creating graph nx object")


#    G = nx.Graph()
#
#    # Add some nodes and relationships (edges)
#    edges: list[tuple[str, str, float]] = [
#        ("Alice", "Bob", 0.1),
#        ("Bob", "Charlie", 0.1),
#        ("Charlie", "David", 0.1),
#        ("David", "Alice", 0.1),
#        ("Alice", "Charlie", 0.1),
#        ("Eve", "Alice", 0.1),
#    ]
#    G.add_weighted_edges_from(edges)
#
#    # Create a Pyvis network object
    net = Network(notebook=False, height="750px", width="100%")

    # Load the NetworkX graph into Pyvis
    net.from_nx(G)

    logging.debug("Done loading")

    # Save and open the interactive graph in your browser
    net.write_html("interactive_graph.html", open_browser=True)
    logging.debug("Done creating HTML")

if __name__ == "__main__":
    main()
