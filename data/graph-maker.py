from neo4j import GraphDatabase
import networkx as nx
from pyvis.network import Network
import os
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def build_graph():
    def run_query(tx):
        result = tx.run("MATCH (n)-[r]->(m) RETURN n.name AS source, type(r) AS rel, m.name AS target")
        G = nx.DiGraph()
        for record in result:
            G.add_edge(record["source"], record["target"], label=record["rel"])
        return G

    with driver.session() as session:
        graph = session.read_transaction(run_query)
    return graph

def save_graph_as_html(graph, output_path="neo4j_graph.html"):
    net = Network(notebook=False, directed=True)
    net.from_nx(graph)

    for node in net.nodes:
        node["color"] = "#c27aff"
        node["font"] = {"color": "#ffffff"}

    net.save_graph(output_path)
    print(f"Graph saved to: {output_path}")


if __name__ == "__main__":
    graph = build_graph()
    save_graph_as_html(graph, "neo4j_graph.html")