# Dataset

Current dataset I plan on using for the final training run: [Spotify's million playlist dataset](https://www.aicrowd.com/challenges/spotify-million-playlist-dataset-challenge/dataset_files)

For training, I plan on using a smaller version of this dataset.

# Current dataset generation workflow

1. Setup environment
    - Generate a virtual environment and install the requirements in `requirements.txt`
2. Download raw dataset
    - Requires registering for the [challenge](https://www.aicrowd.com/challenges/spotify-million-playlist-dataset-challenge/dataset_files)
3. Clean the dataset, and generate two complementary datasets (playlist -> songs & songs -> playlists)
    - Run `python process_raw_dataset.py --help` for more info on args
    - `rd`, `c`, and `o` are important
    - `cd` is useful when a clean dataset already exists, and an inverted dataset is required
4. Generate the graph matrices and mapping files
    - Run `python gen_graph_mat.py --help`
5. Optionally visualize the graph to get a feel for what it looks like
    - Run `python visualize_graph_mat.py --help`
