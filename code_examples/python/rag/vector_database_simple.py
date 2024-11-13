from dotenv import load_dotenv
from langchain_community.vectorstores import Pinecone
from langchain_openai import OpenAIEmbeddings
from typing import List, Dict, Any
import uuid
from pinecone import Pinecone as PineconeClient

load_dotenv()

class VectorStoreSimple:
    """
    A class to store and search text using vector embeddings.
    Uses Pinecone for vector storage and OpenAI for generating embeddings via LangChain.
    """

    def __init__(self):
        self.index_name = "berkshire-hathaway"
        # Initialize Pinecone client
        pc = PineconeClient()
        
        # Initialize LangChain components
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vector_store = Pinecone(
            pc.Index(self.index_name),
            self.embeddings,
            "text"  # metadata field that holds the text
        )

    def add_to_index(self, text: str, metadata: Dict[str, Any] = None) -> None:
        # Combine text with metadata if provided
        full_metadata = metadata or {}
        full_metadata["text"] = text
        
        # Add to vector store using LangChain
        self.vector_store.add_texts(
            texts=[text],
            metadatas=[full_metadata],
            ids=[str(uuid.uuid4())]
        )

    def similarity_search(self, query: str, top_k: int = 5) -> List[Dict]:
        # Use LangChain's similarity search
        results = self.vector_store.similarity_search_with_score(
            query,
            k=top_k
        )
        
        return [
            {
                "score": score,  # Lower score = more similar
                "metadata": doc.metadata  # The metadata we stored with the text
            }
            for doc, score in results
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