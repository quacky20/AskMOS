import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from neo4j import GraphDatabase
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Setup Neo4j & LLM
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name="meta-llama/llama-4-maverick-17b-128e-instruct")

def generate_cypher(nl_query):
    prompt = f"""
You are a Cypher expert. Convert the following natural language question into a single valid Cypher query.

Only output the query — do NOT add explanation, markdown, or commentary.

- Node Label: Entity
- Relationship: RELATES with a property `type`

Question: {nl_query}
"""
    response = llm.predict(prompt).strip()

    # If the model added extra text, try to extract only code
    for line in response.splitlines():
        if line.strip().startswith("MATCH"):
            return response.strip()  # Assume full query is usable
    return ""  # If nothing usable, return empty

def run_cypher(cypher_query):
    with driver.session() as session:
        result = session.run(cypher_query)
        return [record.data() for record in result]

def generate_answer(question, graph_data):
    try:
        trimmed = graph_data[:5]
        graph_summary = json.dumps(trimmed, indent=2)

        prompt = f"""
You are an AI assistant helping users answer questions based on knowledge graph data.

Here is the user's question:
{question}

And here is relevant graph data (first 5 entries):
{graph_summary}

Based on the graph data, provide a direct and concise answer to the question above.
"""

        answer = llm.predict(prompt).strip()
        return answer if answer else "Sorry, I couldn't generate an answer from the current data."

    except Exception as e:
        return f"⚠️ Error generating answer: {str(e)}"

def draw_subgraph(entity_name, depth=2):
    G = nx.DiGraph()

    try:
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

    except Exception as e:
        st.warning(f"⚠️ Could not draw subgraph for '{entity_name}': {e}")
        return None

# Streamlit UI
st.set_page_config(page_title="Graph-RAG QA", layout="wide")
st.title("🧠 Graph-RAG Help Bot (MOSDAC)")

query = st.text_input("Ask a question related to MOSDAC data", "")

if query:
    with st.spinner("🔍 Generating Cypher query..."):
        cypher = generate_cypher(query)
    st.code(cypher, language="cypher")

    with st.spinner("🧠 Querying Neo4j..."):
        result = run_cypher(cypher)

    if result:
        st.success("✅ Graph data retrieved!")

        # st.subheader("📊 Query Results")
        # st.dataframe(result)

        with st.spinner("💬 Generating final answer..."):
            final_answer = generate_answer(query, result)
        st.subheader("🗨️ Final Answer")
        if final_answer.startswith("⚠️"):
            st.warning(final_answer)
        else:
            st.success(final_answer)

        st.subheader("🕸️ Subgraph Visualization")
        entity_default = ""
        if result and list(result[0].values()):
            entity_default = str(list(result[0].values())[0])
        entity = st.text_input("Entity to visualize:", value=entity_default)

        if entity.strip():
            fig = draw_subgraph(entity.strip(), depth=2)
            if fig:
                st.pyplot(fig)
    else:
        st.warning("⚠️ No data found in the graph for this query.")