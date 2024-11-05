from dotenv import load_dotenv
from pinecone import Pinecone
import openai
from typing import List, Dict, Any
import uuid

load_dotenv()

class VectorStoreSimple:
    """
    A class to store and search text using vector embeddings.
    Uses Pinecone for vector storage and OpenAI for generating embeddings.
    """

    def __init__(self):
        self.index_name = "berkshire-hathaway"
        pc = Pinecone()
        self.index = pc.Index(self.index_name)
        
        self.client = openai.OpenAI()
        
    def _get_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model="text-embedding-3-small",  # Using OpenAI's latest small embedding model
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding

    def add_to_index(self, text: str, metadata: Dict[str, Any] = None) -> None:
        embedding = self._get_embedding(text)
        vector_id = str(uuid.uuid4())
        self.index.upsert(
            vectors=[(vector_id, embedding, metadata or {"text": text})]
        )

    def similarity_search(self, query: str, top_k: int = 5) -> List[Dict]:
        query_embedding = self._get_embedding(query)
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        return [
            {
                "score": match.score,  # How similar this result is (lower = more similar)
                "metadata": match.metadata  # The metadata we stored with the text
            }
            for match in results.matches
        ]
    
if __name__ == "__main__":
    # Create an instance of the VectorStoreSimple
    vector_store = VectorStoreSimple()
    
    # Perform a similarity search
    query = "Why does warren like coke so much?"
    query = "What holdings did bershire hathaway have in 1986?"
    query = "Where is bershire hathaway HQ located?"
    query = "What are some companies that bershire hathway has sold in the 80s?"
    query = "What is warren's opinion of the government?"
    query = "Who is warrent buffet's partner?"
    query = "What insurance companies has bershire hathaway invested in over the years?"
    results = vector_store.similarity_search(query, top_k=2)
    
    # Print the results
    for result in results:
        print(f"Score: {result['score']}, Year: {result['metadata']['year']}")