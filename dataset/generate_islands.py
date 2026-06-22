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
import numpy as np

# Essentially if I want to find where all the connections are, I need to do csr.indices[csr.indptr[row]:csr.indptr[row+1]] where row and index are 0 indexed row and column indices.

# Song list is an array


logging.basicConfig(
  level=logging.DEBUG,
  format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

def get_neighbors(graph_mat: csr_matrix, song_idx: int) -> list[tuple[int, int]]:
    start = graph_mat.indptr[song_idx]
    end = graph_mat.indptr[song_idx + 1]
    return [
          (int(neighbor_idx), int(weight))
          for neighbor_idx, weight in zip(graph_mat.indices[start:end], graph_mat.data[start:end])
      ]

def select_neighborhood(
    graph_mat,
    seed_indices: list[int],
    depth: int = -1,
    max_nodes: int = -1,
    max_edges: int = -1,
    progress_interval: int = 10000,
):
    selected_nodes = set(seed_indices)
    selected_edges = {}
    queue = deque((seed_idx, 0) for seed_idx in seed_indices)
    expanded_nodes = set()

    while queue and (len(selected_nodes) < max_nodes or max_nodes == -1) and (len(selected_edges) < max_edges or max_edges == -1):
        node_idx, node_depth = queue.popleft()
        if node_idx in expanded_nodes or (node_depth >= depth and depth != -1):
            continue

        expanded_nodes.add(node_idx)
        if progress_interval > 0 and len(expanded_nodes) % progress_interval == 0:
            logger.debug(
                "Expanded %s nodes, selected %s nodes and %s edges; queue size is %s",
                f"{len(expanded_nodes):,}",
                f"{len(selected_nodes):,}",
                f"{len(selected_edges):,}",
                f"{len(queue):,}",
            )

        neighbors = get_neighbors(
            graph_mat,
            node_idx
        )

        for neighbor_idx, weight in neighbors:
            if len(selected_edges) >= max_edges and max_edges != -1:
                break

            if neighbor_idx not in selected_nodes:
                if len(selected_nodes) >= max_nodes and max_nodes != -1:
                    continue
                selected_nodes.add(neighbor_idx)
                queue.append((neighbor_idx, node_depth + 1))

            edge_key = tuple(sorted((node_idx, neighbor_idx)))
            selected_edges[edge_key] = max(weight, selected_edges.get(edge_key, 0))

    return selected_nodes, selected_edges
    

def main():
    parser = argparse.ArgumentParser(description="A script meant to take in the processed dataset connection graph matrix and generate island lists.")

    parser.add_argument("mat_save_dir", type=Path, help="The path the output graph gets stored in.")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        help="Logging verbosity.",
    )
    parser.add_argument(
        "--progress-interval",
        type=int,
        default=10000,
        help="Log traversal progress every N expanded nodes. Use 0 to disable.",
    )
    parser.add_argument(
        "--top-k-islands",
        type=int,
        default=10,
        help="Log the top K largest islands by song count. Use 0 to disable.",
    )

    args = parser.parse_args()

    logging.getLogger().setLevel(getattr(logging, args.log_level))

    logger.info("Loading graph artifacts from %s", args.mat_save_dir)
    graph_mat = load_npz(args.mat_save_dir / "graph_mat.npz")

    with open(args.mat_save_dir / "top_connected_songs.json", "r") as f:
        top_connected_songs = json.load(f)

    with open(args.mat_save_dir / "song_to_idx.json", "r") as f:
        song_to_idx = json.load(f)

    with open(args.mat_save_dir / "idx_to_song.json", "r") as f:
        idx_to_song = json.load(f)

    # TODO: Subtract identity matrix (maybe need to scale by # playlists ? idk)
    unvisited = set(range(graph_mat.shape[0]))
    total_nodes = graph_mat.shape[0]
    islands = 0
    island_summaries = []

    logger.info(
        "Loaded matrix with %s nodes and %s nonzero edges/entries",
        f"{total_nodes:,}",
        f"{graph_mat.nnz:,}",
    )

    while unvisited:
        seed = next(iter(unvisited))
        logger.info(
            "Starting island %s from matrix index %s; %s/%s nodes remain unvisited",
            islands + 1,
            seed,
            f"{len(unvisited):,}",
            f"{total_nodes:,}",
        )

        selected_nodes, selected_edges = select_neighborhood(
            graph_mat,
            [seed],
            progress_interval=args.progress_interval,
        )
        unvisited.difference_update(selected_nodes)
        islands += 1
        island_summaries.append(
            {
                "island_number": islands,
                "seed_idx": seed,
                "seed_song_id": idx_to_song[str(seed)],
                "song_count": len(selected_nodes),
                "edge_count": len(selected_edges),
            }
        )

        logger.info(
            "Finished island %s: %s nodes, %s edges; %s/%s nodes visited",
            islands,
            f"{len(selected_nodes):,}",
            f"{len(selected_edges):,}",
            f"{total_nodes - len(unvisited):,}",
            f"{total_nodes:,}",
        )

    logger.info(
        "Found %s islands. Largest island has %s nodes.",
        f"{islands:,}",
        f"{max((summary['song_count'] for summary in island_summaries), default=0):,}",
    )

    if args.top_k_islands > 0:
        top_islands = sorted(
            island_summaries,
            key=lambda summary: summary["song_count"],
            reverse=True,
        )[:args.top_k_islands]

        logger.info("Top %s islands by song count:", len(top_islands))
        for rank, island in enumerate(top_islands, start=1):
            logger.info(
                "#%s island %s: %s songs, %s edges, seed matrix index %s, seed song id %s",
                rank,
                island["island_number"],
                f"{island['song_count']:,}",
                f"{island['edge_count']:,}",
                island["seed_idx"],
                island["seed_song_id"],
            )

    print(islands)



if __name__ == "__main__":
    main()
