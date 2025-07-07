import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from neo4j import GraphDatabase
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Neo4j & LLM
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name="llama3-8b-8192")

def generate_cypher(nl_query):
    prompt = f"""
You are a Cypher query generator. Translate the following natural language question into a Cypher query.

- Nodes are labeled `Entity`
- Relationships are labeled `RELATES` and have a property `type`

Question: {nl_query}
Cypher:
"""
    return llm.predict(prompt).strip()

def run_cypher(cypher_query):
    with driver.session() as session:
        result = session.run(cypher_query)
        return [record.data() for record in result]

def generate_answer(question, graph_data):
    prompt = f"""
Use the following knowledge graph data to answer the user query.

Question: {question}
Graph Data: {graph_data}
Answer:
"""
    return llm.predict(prompt).strip()

def draw_subgraph(entity_name, depth=2):
    G = nx.DiGraph()

    with driver.session() as session:
        query = f"""
        MATCH path = (start:Entity {{name: $entity_name}})-[*1..{depth}]-(connected)
        RETURN path
        """
        results = session.run(query, entity_name=entity_name)
        for record in results:
            path = record["path"]
            for rel in path.relationships:
                s = rel.start_node["name"]
                o = rel.end_node["name"]
                r = rel["type"]
                G.add_node(s)
                G.add_node(o)
                G.add_edge(s, o, label=r)
    
    pos = nx.spring_layout(G, k=0.5)
    edge_labels = nx.get_edge_attributes(G, 'label')
    
    fig, ax = plt.subplots(figsize=(10, 6))
    nx.draw(G, pos, with_labels=True, node_size=2000, node_color="skyblue", font_size=10, font_weight="bold", ax=ax)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', ax=ax)
    return fig

# Streamlit UI
st.set_page_config(page_title="Graph-RAG QA", layout="wide")
st.title("🧠 Graph-RAG Help Bot (MOSDAC)")

query = st.text_input("Ask a question related to MOSDAC data", "")

if query:
    with st.spinner("Generating Cypher query from your question..."):
        cypher = generate_cypher(query)
    st.code(cypher, language="cypher")

    with st.spinner("Querying Neo4j..."):
        result = run_cypher(cypher)

    if result:
        st.success("Graph data retrieved!")

        st.subheader("📊 Query Results")
        st.dataframe(result)

        with st.spinner("Generating final answer..."):
            final_answer = generate_answer(query, result)
        st.subheader("💬 Final Answer")
        st.info(final_answer)

        st.subheader("🕸️ Subgraph Visualization")
        entity = st.text_input("Visualize subgraph from entity (default: first node)", value=list(result[0].values())[0] if result else "")
        if entity:
            fig = draw_subgraph(entity_name=entity, depth=2)
            st.pyplot(fig)
    else:
        st.warning("No data found in graph for this query.")