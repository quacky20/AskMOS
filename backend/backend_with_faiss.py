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

FAISS_INDEX_PATH = "faiss_index"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="meta-llama/llama-4-maverick-17b-128e-instruct",
    temperature=0.1,
)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vector_store = None
entity_cache = {}
relationship_cache = {}

import os

def initialize_vector_store(force_rebuild=False):
    global vector_store, entity_cache, relationship_cache

    try:
        if os.path.exists(FAISS_INDEX_PATH) and not force_rebuild:
            print("Loading FAISS index from disk...")
            vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
            print("FAISS index loaded.")
            return
        
        print("Building FAISS index from Neo4j...")

        entities = get_all_entities()
        entity_cache = {entity['name'].lower(): entity for entity in entities}

        relationships = get_all_relationship_types()
        relationship_cache = {rel['type'].lower(): rel for rel in relationships}

        documents = []

        for entity in entities:
            doc = Document(
                page_content=f"Entity: {entity['name']} {entity.get('description', '') or ''}",
                metadata={"type": "entity", "name": entity['name'], "id": entity.get('id')}
            )
            documents.append(doc)

        for rel in relationships:
            doc = Document(
                page_content=f"Relationship: {rel['type']}",
                metadata={"type": "relationship", "name": rel['type']}
            )
            documents.append(doc)

        if documents:
            vector_store = FAISS.from_documents(documents, embeddings)
            print(f"Vector store initialized with {len(documents)} documents")

            vector_store.save_local(FAISS_INDEX_PATH)
            print("FAISS index saved to disk.")
        else:
            print("No documents found to create vector store.")

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
    
    response = llm.invoke(prompt).content.strip()

    entities = []
    for entity in response.split(','):
        entity = entity.strip().strip('"').strip("'")
        if entity and len(entity) > 1:
            entities.append(entity)
    
    return entities

def find_matching_entities(extracted_entities: List[str]) -> List[Dict]:
    matched_entities = []
    
    for entity in extracted_entities:
        if entity.lower() in entity_cache:
            matched_entities.append({
                "original": entity,
                "matched": entity_cache[entity.lower()]['name'],
                "type": "entity",
                "confidence": 1.0
            })
        else:
            search_results = semantic_search(entity, k=3)
            for result in search_results:
                if result["type"] == "entity":
                    matched_entities.append({
                        "original": entity,
                        "matched": result["name"],
                        "type": "entity",
                        "confidence": 0.8
                    })
                    break
    
    return matched_entities

def semantic_search(query: str, k: int = 10) -> List[Dict]:
    """Perform semantic search to find relevant entities and relationships"""
    if not vector_store:
        return []
    
    try:
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

def execute_query_with_proper_fallback(query: str, matched_entities: List[Dict]) -> tuple:
    with driver.session() as session:
        
        if matched_entities:
            entity_name = matched_entities[0]["matched"]
            
            relationship_query = f"""
            MATCH (n)-[r]-(m) 
            WHERE toLower(n.name) = toLower('{entity_name}') 
            RETURN n, type(r) as relationship_type, m
            """
            
            print(f"Executing relationship query: {relationship_query}")
            
            try:
                result = session.run(relationship_query)
                data = [record.data() for record in result]
                
                if data:
                    print(f"Found {len(data)} relationships for {entity_name}")
                    return data, "entity_relationships"
                else:
                    print(f"No relationships found for {entity_name}, checking if entity exists...")
                    
                    entity_query = f"""
                    MATCH (n) 
                    WHERE toLower(n.name) = toLower('{entity_name}') 
                    RETURN n
                    """
                    
                    entity_result = session.run(entity_query)
                    entity_data = [record.data() for record in entity_result]
                    
                    if entity_data:
                        print(f"Entity {entity_name} exists but has no relationships")
                        return entity_data, "entity_no_relationships"
                    else:
                        print(f"Entity {entity_name} not found")
                        return get_all_relationships(session)
                        
            except Exception as e:
                print(f"Error executing relationship query: {e}")
                return get_all_relationships(session)
        
        else:
            print("No matched entities found, returning all relationships")
            return get_all_relationships(session)

def get_all_relationships(session):
    try:
        all_relationships_query = """
        MATCH (n)-[r]->(m) 
        RETURN n, type(r) as relationship_type, m 
        LIMIT 20
        """
        
        print("Executing query for all relationships")
        result = session.run(all_relationships_query)
        data = [record.data() for record in result]
        
        if data:
            print(f"Found {len(data)} general relationships")
            return data, "all_relationships"
        else:
            print("No relationships found in the entire graph")
            return [], "no_data"
            
    except Exception as e:
        print(f"Error getting all relationships: {e}")
        return [], "error"

def generate_answer(question: str, graph_data: List[Dict], query_type: str) -> str:

    if not graph_data:
        return "No data found in the knowledge graph."

    limited_data = graph_data[:10]
    
    try:
        graph_json = json.dumps(limited_data, indent=2, default=str)
    except:
        graph_json = str(limited_data)
    
    if query_type == "entity_relationships":
        prompt = f"""
Based on the knowledge graph data below, answer the user's question directly and concisely.

User's question: {question}

Knowledge graph data:
{graph_json}

Instructions:
- Answer based ONLY on the provided graph data
- Be direct and concise
- Do not add external knowledge
- If the data shows relationships, describe them clearly
- If asking about a specific entity, focus on what the data shows about that entity

Answer:"""

    elif query_type == "entity_no_relationships":
        prompt = f"""
The entity from the user's question exists in the knowledge graph but has no relationships with other entities.

User's question: {question}

Entity data:
{graph_json}

Provide a brief response indicating that the entity exists but has no connections in the current knowledge graph.

Answer:"""

    elif query_type == "all_relationships":
        prompt = f"""
The user asked about something not specifically found in the knowledge graph. Here are the available relationships in the knowledge graph:

User's question: {question}

Available relationships:
{graph_json}

Instructions:
- Mention that the specific entity/concept wasn't found
- Briefly describe what relationships are available in the knowledge graph
- Be concise and factual

Answer:"""

    else:
        prompt = f"""
Answer the user's question based on the available knowledge graph data:

User's question: {question}

Data:
{graph_json}

Answer:"""
    
    try:
        response = llm.invoke(prompt).content.strip()
        return response if response else "Unable to generate answer from the available data."
    except Exception as e:
        print(f"Error generating answer: {e}")
        return "Sorry, I encountered an error while generating the answer."

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        if not vector_store:
            initialize_vector_store()
        
        extracted_entities = extract_entities_from_query(query)
        print(f"Extracted entities: {extracted_entities}")
        
        matched_entities = find_matching_entities(extracted_entities)
        print(f"Matched entities: {matched_entities}")
        
        result, query_type = execute_query_with_proper_fallback(query, matched_entities)
        
        final_answer = generate_answer(query, result, query_type)
        
        return jsonify({
            "answer": final_answer,
            "debug": {
                "extracted_entities": extracted_entities,
                "matched_entities": matched_entities,
                "query_type": query_type,
                "result_count": len(result)
            }
        })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error processing query: {str(e)}"}), 500

@app.route('/refresh-vector-store', methods=['POST'])
def refresh_vector_store():
    try:
        initialize_vector_store(force_rebuild=True)
        return jsonify({"message": "Vector store refreshed and saved successfully"})
    except Exception as e:
        return jsonify({"error": f"Error refreshing vector store: {str(e)}"}), 500

if __name__ == '__main__':
    initialize_vector_store()
    app.run(debug=True)