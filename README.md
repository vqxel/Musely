# Musely
*Temp Name & README*

Arbitrary music -> embedding model trained using contrastive learning. Inspired by JEPA architecture model training (even though it's not a world model).

# Dataset Approach
I plan on training this model using contrastive learning. As such, I need to be able to identify whether a song is similar to another song (and potentially how similar they are). I plan on doing this through a weighted graph between songs. I will take a dataset (planning on using [Spotify's million song dataset](https://www.aicrowd.com/challenges/spotify-million-playlist-dataset-challenge/dataset_files)) for now and create a graphthat connects all songs to all other songs that share playlists. I will classify how similar two songs are by A) their distance on the graph and B) the strength of the connections between the songs (based on # of shared playlists). 

To start, I plan on using a smaller version of this dataset to try to verify that this approach works and try to visualize what the dataset looks like relationship wise. I will also use this to get a feel for hyper parameters I'll need such as how strong relationships should be and at what point (distance) two songs should no longer be related.
