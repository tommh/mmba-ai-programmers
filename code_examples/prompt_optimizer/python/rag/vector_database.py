from dotenv import load_dotenv
from pinecone import Pinecone
import openai
from typing import List, Dict, Any

load_dotenv()

class VectorStore:
    """
    A class to store and search text using vector embeddings.
    Uses Pinecone for vector storage and OpenAI for generating embeddings.
    """

    def __init__(self):
        """
        Initialize the vector store with OpenAI API key.
        
        Args:
            api_key (str): Your OpenAI API key
        """
        # Name of our Pinecone index where vectors will be stored
        self.index_name = "berkshire-hathaway"
        
        # Set up OpenAI client for generating embeddings
        self.client = openai.OpenAI()

        pc = Pinecone()
        
        # Connect to our Pinecone index
        self.index = pc.Index(self.index_name)
        
    def _get_embedding(self, text: str) -> List[float]:
        """
        Convert text into a vector embedding using OpenAI's API.
        
        Args:
            text (str): The text to convert into an embedding
            
        Returns:
            List[float]: A list of numbers representing the text embedding
        """
        # Call OpenAI's API to generate the embedding
        response = self.client.embeddings.create(
            model="text-embedding-3-small",  # Using OpenAI's latest small embedding model
            input=text,
            encoding_format="float"
        )
        # Extract and return just the embedding vector
        return response.data[0].embedding

    def add_to_index(self, text: str, metadata: Dict[str, Any] = None) -> None:
        """
        Add a piece of text to our vector database.
        
        Args:
            text (str): The text to store
            metadata (Dict[str, Any], optional): Additional information about the text
                Example: {"source": "annual_letter", "year": 2023}
        """
        # Step 1: Convert the text to an embedding
        embedding = self._get_embedding(text)

        if metadata:
            metadata['text'] = text
        
        # Step 2: Generate a unique ID for this piece of text
        import uuid
        vector_id = str(uuid.uuid4())
        
        # Step 3: Store in Pinecone
        # If no metadata is provided, we'll store the text itself as metadata
        self.index.upsert(
            vectors=[(vector_id, embedding, metadata or {"text": text})]
        )

    def similarity_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for text similar to the query.
        
        Args:
            query (str): The text to search for
            top_k (int): Number of similar results to return
            
        Returns:
            List[Dict]: List of similar items, each with a similarity score and metadata
        """
        # Step 1: Convert the search query to an embedding
        query_embedding = self._get_embedding(query)
        
        # Step 2: Search Pinecone for similar vectors
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Step 3: Format and return the results
        return [
            {
                "score": match.score,  # How similar this result is (lower = more similar)
                "metadata": match.metadata  # The metadata we stored with the text
            }
            for match in results.matches
        ]