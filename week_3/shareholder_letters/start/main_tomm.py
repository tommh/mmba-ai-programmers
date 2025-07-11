import os
import glob
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

# Load environment variables from .env
load_dotenv()

# Constants
INDEX_NAME = "classdocuments"
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini-2024-07-18"

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Initialize Pinecone client
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))

# Create Pinecone index if not exists
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

# Get index object
index = pc.Index(INDEX_NAME)

def load_documents():
    documents = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "letters/*.txt")
    files = glob.glob(path)

    for file_path in files:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            documents.append({"content": content, "metadata": {"source": file_path}})

    print(f"Found {len(documents)} letters")
    return documents

def chunk_documents(documents, chunk_size=1000, chunk_overlap=200):
    chunks = []
    for doc in documents:
        content = doc["content"]
        metadata = doc["metadata"]

        for i in range(0, len(content), chunk_size - chunk_overlap):
            start = max(i - chunk_overlap, 0)
            chunk_content = content[start:start + chunk_size]
            if chunk_content:
                chunks.append({"content": chunk_content, "metadata": metadata})
    return chunks

def get_embeddings(texts: List[str]):
    response = client.embeddings.create(
        input=texts,
        model=EMBEDDING_MODEL
    )
    return [record.embedding for record in response.data]

def embed_documents(chunks, namespace):
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        chunk_batch = chunks[i:i+batch_size]
        texts = [chunk["content"] for chunk in chunk_batch]
        embeddings = get_embeddings(texts)

        vectors = [{
            "id": f"chunk_{i + j}",
            "values": embeddings[j],
            "metadata": {
                **chunk_batch[j]["metadata"],
                "content": chunk_batch[j]["content"]
            }
        } for j in range(len(chunk_batch))]

        index.upsert(vectors=vectors, namespace=namespace)

def search_documents(query, namespace, top_k=5):
    query_embedding = get_embeddings([query])[0]
    search_results = index.query(
        vector=query_embedding,
        top_k=top_k,
        namespace=namespace,
        include_metadata=True
    )
    return [(match['metadata'].get('content', ''), match['score']) for match in search_results['matches']]

def ask_openai(query, documents):
    context = "\n\n".join([doc for doc, _ in documents])
    messages = [
        {"role": "system", "content": "Provide an answer to the user's query about Berkshire Hathaway. Use the shareholder meeting documents."},
        {"role": "system", "content": f"Documents: {context}"},
        {"role": "user", "content": query}
    ]
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    # docs = load_documents()
    # chunks = chunk_documents(docs)
    # embed_documents(chunks, namespace="chunks")

    user_query = "When did Berkshire Hathaway purchase its first Coke stock?"
    docs_and_scores = search_documents(query=user_query, namespace="chunks")
    for _, score in docs_and_scores:
        print(f"Score: {score}")
    response = ask_openai(user_query, docs_and_scores)
    print(response)
