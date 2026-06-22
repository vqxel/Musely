# NOTE: This was generated with Codex

import argparse
import json
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def load_json_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        raise FileNotFoundError(f"Directory does not exist: {directory}")

    filepaths = sorted(path for path in directory.rglob("*.json") if path.is_file())
    if not filepaths:
        raise FileNotFoundError(f"No JSON files found in: {directory}")

    return filepaths


def read_json_object(path: Path):
    with open(path, "r") as f:
        chunk = json.load(f)

    if not isinstance(chunk, dict):
        raise ValueError(f"Expected top-level JSON object in {path}")

    return chunk


def collect_mapping_stats(mapping_dir: Path, key_name: str, value_name: str):
    key_ids = set()
    value_ids = set()
    duplicate_keys = 0
    edge_count = 0
    min_values_per_key = None
    max_values_per_key = 0

    filepaths = load_json_files(mapping_dir)
    logger.info("Processing %s %s files from %s", len(filepaths), key_name, mapping_dir)

    for path in filepaths:
        logger.debug("Reading %s", path)
        chunk = read_json_object(path)

        for key, values in chunk.items():
            if not isinstance(values, list):
                raise ValueError(
                    f"Expected {value_name} list for {key_name} {key!r} in {path}"
                )

            if key in key_ids:
                duplicate_keys += 1

            key_ids.add(str(key))

            value_count = len(values)
            edge_count += value_count
            min_values_per_key = (
                value_count
                if min_values_per_key is None
                else min(min_values_per_key, value_count)
            )
            max_values_per_key = max(max_values_per_key, value_count)

            for value in values:
                value_ids.add(str(value))

    return {
        "files": len(filepaths),
        "key_name": key_name,
        "value_name": value_name,
        "key_label": key_name[:-1],
        "value_label": value_name[:-1],
        "unique_keys": len(key_ids),
        "unique_values": len(value_ids),
        "duplicate_keys": duplicate_keys,
        "edges": edge_count,
        "min_values_per_key": min_values_per_key or 0,
        "max_values_per_key": max_values_per_key,
        "avg_values_per_key": edge_count / len(key_ids) if key_ids else 0,
    }


def log_mapping_stats(stats):
    logger.info("%s files: %s", stats["key_name"].capitalize(), stats["files"])
    logger.info("Unique %s: %s", stats["key_name"], f"{stats['unique_keys']:,}")
    logger.info("Unique %s: %s", stats["value_name"], f"{stats['unique_values']:,}")
    logger.info("Total relationships: %s", f"{stats['edges']:,}")
    logger.info(
        "%s per %s: avg %.2f, min %s, max %s",
        stats["value_name"].capitalize(),
        stats["key_label"],
        stats["avg_values_per_key"],
        stats["min_values_per_key"],
        stats["max_values_per_key"],
    )

    if stats["duplicate_keys"]:
        logger.warning(
            "Found %s duplicate %s keys across JSON chunks",
            f"{stats['duplicate_keys']:,}",
            stats["key_name"],
        )


def log_dataset_stats(playlists_to_songs_stats, songs_to_playlists_stats):
    playlist_count = playlists_to_songs_stats["unique_keys"]
    song_count = songs_to_playlists_stats["unique_keys"]
    playlist_song_edges = playlists_to_songs_stats["edges"]
    song_playlist_edges = songs_to_playlists_stats["edges"]

    logger.info("Dataset stats")
    logger.info("Playlists: %s", f"{playlist_count:,}")
    logger.info("Songs: %s", f"{song_count:,}")
    logger.info("Playlist-song relationships: %s", f"{playlist_song_edges:,}")

    logger.info(
        "Avg songs per playlist: %.2f",
        playlist_song_edges / playlist_count if playlist_count else 0,
    )
    logger.info(
        "Avg playlists per song: %.2f",
        song_playlist_edges / song_count if song_count else 0,
    )

    if playlists_to_songs_stats["unique_values"] != song_count:
        logger.warning(
            "Warning: song counts differ between playlist->songs and "
            "songs->playlists datasets."
        )
        logger.warning(
            "Songs from playlist dataset: %s",
            f"{playlists_to_songs_stats['unique_values']:,}",
        )

    if songs_to_playlists_stats["unique_values"] != playlist_count:
        logger.warning(
            "Warning: playlist counts differ between playlist->songs and "
            "songs->playlists datasets."
        )
        logger.warning(
            "Playlists from song dataset: %s",
            f"{songs_to_playlists_stats['unique_values']:,}",
        )

    if song_playlist_edges != playlist_song_edges:
        logger.warning(
            "Warning: edge counts differ between playlist->songs and "
            "songs->playlists datasets."
        )
        logger.warning("Song->playlist relationships: %s", f"{song_playlist_edges:,}")


def main():
    parser = argparse.ArgumentParser(
        description="Print basic stats for generated playlist/song dataset JSON chunks."
    )
    parser.add_argument(
        "playlists_to_songs",
        type=Path,
        help="The path to the playlist -> songs dataset JSON chunks.",
    )
    parser.add_argument(
        "songs_to_playlists",
        type=Path,
        help="The path to the songs -> playlists dataset JSON chunks.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level.",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    playlists_to_songs_stats = collect_mapping_stats(
        args.playlists_to_songs,
        key_name="playlists",
        value_name="songs",
    )
    log_mapping_stats(playlists_to_songs_stats)

    songs_to_playlists_stats = collect_mapping_stats(
        args.songs_to_playlists,
        key_name="songs",
        value_name="playlists",
    )
    log_mapping_stats(songs_to_playlists_stats)

    log_dataset_stats(playlists_to_songs_stats, songs_to_playlists_stats)


if __name__ == "__main__":
    main()
