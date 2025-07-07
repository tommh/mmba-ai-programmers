# Example documents about movies
texts = [
    "Olsenbanden er god gammeldags moro",
    "Flåklypa Grand Prix er dukkefilm", 
    "Orions Belte er en klassiker",
    "Den forsvunne pølsemaker er morsom"
]

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_embedding(text):
    client = OpenAI()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# Generate embeddings for all texts
embeddings = []
for text in texts:
    embedding = get_embedding(text)
    embeddings.append(embedding)

import faiss
import numpy as np

# Create FAISS index
dimension = len(embeddings[0])
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings, dtype='float32'))

# Query the index
query = 'Sjeik Ben Reddik Fy Fasan'
query_embedding = get_embedding(query)
distances, indices = index.search(np.array([query_embedding], dtype='float32'), 4)  # Changed to 4

# Print results
for i in range(4):  # Now matches the search count
    print(f"Match {i+1}, Distance: {distances[0][i]:.5f}")
    print(texts[indices[0][i]])
    print()