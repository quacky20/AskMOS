from flask import Flask, request, jsonify
from flask_cors import CORS
from neo4j import GraphDatabase
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
import os
from dotenv import load_dotenv
import json
from typing import List, Dict

load_dotenv()

app = Flask(__name__)
CORS(app)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="meta-llama/llama-4-maverick-17b-128e-instruct",
    temperature=0.1,
)

# Initialize embeddings model
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Global variables for caching
vector_store = None
entity_cache = {}
relationship_cache = {}

def initialize_vector_store():
    """Initialize vector store with all entities and relationships from Neo4j"""
    global vector_store, entity_cache, relationship_cache
    
    try:
        # Get all entities
        entities = get_all_entities()
        entity_cache = {entity['name'].lower(): entity for entity in entities}
        
        # Get all relationship types
        relationships = get_all_relationship_types()
        relationship_cache = {rel['type'].lower(): rel for rel in relationships}
        
        # Create documents for vector store
        documents = []
        
        # Add entities to documents
        for entity in entities:
            doc = Document(
                page_content=f"Entity: {entity['name']} {entity.get('description', '') or ''}",
                metadata={"type": "entity", "name": entity['name'], "id": entity.get('id')}
            )
            documents.append(doc)
        
        # Add relationships to documents
        for rel in relationships:
            doc = Document(
                page_content=f"Relationship: {rel['type']}",
                metadata={"type": "relationship", "name": rel['type']}
            )
            documents.append(doc)
        
        # Create FAISS vector store
        if documents:
            vector_store = FAISS.from_documents(documents, embeddings)
            print(f"Vector store initialized with {len(documents)} documents")
        else:
            print("No documents found to create vector store")
            
    except Exception as e:
        print(f"Error initializing vector store: {e}")

def get_all_entities():
    """Get all entities from Neo4j"""
    with driver.session() as session:
        result = session.run("""
            MATCH (n)
            WHERE n.name IS NOT NULL
            RETURN n.name as name, elementId(n) as id, n
        """)
        return [record.data() for record in result]

def get_all_relationship_types():
    """Get all relationship types from Neo4j"""
    with driver.session() as session:
        result = session.run("""
            MATCH ()-[r]->()
            RETURN DISTINCT type(r) as type
        """)
        return [record.data() for record in result]

def extract_entities_from_query(query: str) -> List[str]:
    """Extract potential entities from user query using LLM"""
    prompt = f"""
Extract all entities, concepts, names, and important terms from the following query.
Return them as a simple comma-separated list with no explanations.

Query: {query}

Entities:"""
    
    response = llm.predict(prompt).strip()
    
    # Clean and split the response
    entities = []
    for entity in response.split(','):
        entity = entity.strip().strip('"').strip("'")
        if entity and len(entity) > 1:
            entities.append(entity)
    
    return entities

def extract_relationships_from_query(query: str) -> List[str]:
    prompt = f"""
Extract all possible relationship types, actions, or connection-related verbs from the following query.
Return them as a simple comma-separated list with no explanations.

Query: {query}

Relationships:
"""
    response = llm.predict(prompt).strip()
    relationships = [rel.strip().strip('"').strip("'") for rel in response.split(",") if len(rel.strip()) > 1]
    return relationships

def semantic_search(query: str, k: int = 10) -> List[Dict]:
    """Perform semantic search to find relevant entities and relationships"""
    if not vector_store:
        return []
    
    try:
        # Search for relevant documents
        docs = vector_store.similarity_search(query, k=k)
        
        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "type": doc.metadata.get("type"),
                "name": doc.metadata.get("name")
            })
        
        return results
    except Exception as e:
        print(f"Error in semantic search: {e}")
        return []

def find_matching_entities(extracted_entities: List[str]) -> List[Dict]:
    """Find matching entities in the knowledge graph"""
    matched_entities = []
    
    for entity in extracted_entities:
        # Direct match
        if entity.lower() in entity_cache:
            matched_entities.append({
                "original": entity,
                "matched": entity_cache[entity.lower()]['name'],
                "type": "entity",
                "confidence": 1.0
            })
        else:
            # Semantic search for similar entities
            search_results = semantic_search(entity, k=3)
            for result in search_results:
                if result["type"] == "entity":
                    matched_entities.append({
                        "original": entity,
                        "matched": result["name"],
                        "type": "entity",
                        "confidence": 0.8  # Lower confidence for semantic matches
                    })
                    break
    
    return matched_entities

def find_matching_relationships(query: str) -> List[Dict]:
    matched_relationships = []

    extracted_relationships = extract_relationships_from_query(query)
    for rel in extracted_relationships:
        search_results = semantic_search(rel, k=2)
        for result in search_results:
            if result["type"] == "relationship":
                matched_relationships.append({
                    "original": rel,
                    "matched": result["name"],
                    "type": "relationship",
                    "confidence": 0.8
                })
                break

    # fallback in case nothing was found
    if not matched_relationships:
        search_results = semantic_search(query, k=5)
        for result in search_results:
            if result["type"] == "relationship":
                matched_relationships.append({
                    "original": "query_context",
                    "matched": result["name"],
                    "type": "relationship",
                    "confidence": 0.6
                })
    return matched_relationships

def generate_cypher_with_entities(nl_query: str, matched_entities: List[Dict], matched_relationships: List[Dict]) -> str:
    """Generate Cypher query with specific entity and relationship matches"""
    
    # Prepare context for the LLM
    entity_context = ""
    if matched_entities:
        entity_names = [e["matched"] for e in matched_entities]
        entity_context = f"Available entities: {', '.join(entity_names)}"
    
    relationship_context = ""
    if matched_relationships:
        rel_names = [r["matched"] for r in matched_relationships]
        relationship_context = f"Available relationships: {', '.join(rel_names)}"
    
    prompt = f"""
You are a Cypher expert. Convert the following natural language question into a valid Cypher query.

Database Schema:
- Nodes have a 'name' property (no specific label)
- Relationships are of types like: {', '.join([r['matched'] for r in matched_relationships]) if matched_relationships else 'RELATES'}

Query Requirements:
- Match nodes based on name (case-insensitive): use toLower(n.name) = toLower('<name>')
- Use relationship types exactly as provided
- Do not use hardcoded node labels like :Entity or :Unknown
- Prefer a simple pattern like: (n)-[:RELATES]->(m)

Question: {nl_query}

Cypher query:
"""
    
    response = llm.predict(prompt).strip()
    
    # Extract the Cypher query from the response
    lines = response.split('\n')
    for line in lines:
        if line.strip().startswith("MATCH"):
            return line.strip()
    
    return response.strip()

def run_cypher(cypher_query):
    """Execute Cypher query against Neo4j"""
    with driver.session() as session:
        result = session.run(cypher_query)
        return [record.data() for record in result]

def generate_answer(question, graph_data):
    """Generate natural language answer from graph data"""
    try:
        trimmed = graph_data[:5]
        graph_summary = json.dumps(trimmed, indent=2)

        prompt = f"""
You are an AI assistant helping users answer questions based on knowledge graph data.

Here is the user's question:
{question}

And here is relevant graph data (first 5 entries):
{graph_summary}

Based on the graph data, provide a direct and concise answer to the question above. Just provide one answer, with no trailing explanations.
"""

        answer = llm.predict(prompt).strip()
        return answer if answer else "Sorry, I couldn't generate an answer from the current data."

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"⚠️ Error generating answer: {str(e)}"

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Initialize vector store if not already done
        if not vector_store:
            initialize_vector_store()
        
        # Step 1: Extract entities from query
        extracted_entities = extract_entities_from_query(query)
        print(f"Extracted entities: {extracted_entities}")
        
        # Step 2: Find matching entities in knowledge graph
        matched_entities = find_matching_entities(extracted_entities)
        print(f"Matched entities: {matched_entities}")
        
        # Step 3: Find matching relationships
        matched_relationships = find_matching_relationships(query)
        print(f"Matched relationships: {matched_relationships}")
        
        # Step 4: Generate Cypher with matched entities and relationships
        cypher = generate_cypher_with_entities(query, matched_entities, matched_relationships)
        print(f"Generated Cypher: {cypher}")
        
        # Step 5: Execute Cypher query
        result = run_cypher(cypher)
        
        if result:
            final_answer = generate_answer(query, result)
            return jsonify({
                "answer": final_answer,
                "debug": {
                    "extracted_entities": extracted_entities,
                    "matched_entities": matched_entities,
                    "matched_relationships": matched_relationships,
                    "cypher_query": cypher,
                    "result_count": len(result)
                }
            })
        else:
            return jsonify({"answer": "⚠️ No data found in the graph for this query."})
            
    except Exception as e:
        return jsonify({"error": f"Error processing query: {str(e)}"}), 500

@app.route('/refresh-vector-store', methods=['POST'])
def refresh_vector_store():
    """Endpoint to refresh the vector store with latest data"""
    try:
        initialize_vector_store()
        return jsonify({"message": "Vector store refreshed successfully"})
    except Exception as e:
        return jsonify({"error": f"Error refreshing vector store: {str(e)}"}), 500

if __name__ == '__main__':
    # Initialize vector store on startup
    initialize_vector_store()
    app.run(debug=True)