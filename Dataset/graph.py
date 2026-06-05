import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt

G = nx.Graph()

# Add some nodes and relationships (edges)
edges: list[tuple[str, str, float]] = [
    ("Alice", "Bob", 0.1),
    ("Bob", "Charlie", 0.1),
    ("Charlie", "David", 0.1),
    ("David", "Alice", 0.1),
    ("Alice", "Charlie", 0.1),
    ("Eve", "Alice", 0.1),
]
G.add_weighted_edges_from(edges)

# Create a Pyvis network object
net = Network(notebook=False, height="750px", width="100%")

# Load the NetworkX graph into Pyvis
net.from_nx(G)

# Save and open the interactive graph in your browser
net.write_html("interactive_graph.html", open_browser=True)
