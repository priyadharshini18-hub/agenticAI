from pypdf import PdfReader
from chromadb import Client
from chromadb.utils import embedding_functions

def create_vector_store():
    docs = []

    # Load PDFs
    pdf_files = ["me/Profile.pdf"]  # add more PDFs here
    for pdf_file in pdf_files:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                docs.append(text)
    
    # Text files
    text_files = ["me/summary.txt", "me/projects.txt", "me/other.txt", "me/leadership.txt"]  # add any text files
    for text_file in text_files:
        with open(text_file, "r", encoding="utf-8") as f:
            docs.append(f.read())

    # Chunk function
    def chunk_text(text, max_tokens=300):
        sentences = text.split(". ")
        chunks = []
        current_chunk = ""
        current_tokens = 0
        for sentence in sentences:
            tokens = len(sentence.split())
            if current_tokens + tokens > max_tokens:
                chunks.append(current_chunk)
                current_chunk = sentence
                current_tokens = tokens
            else:
                current_chunk += " " + sentence
                current_tokens += tokens
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    chunked_docs = []
    for doc in docs:
        chunked_docs.extend(chunk_text(doc))

    # Create Chroma collection
    client = Client()
    embeddings = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = client.create_collection(name="personal_kb", embedding_function=embeddings)

    for i, chunk in enumerate(chunked_docs):
        collection.add(
            documents=[chunk],
            metadatas=[{"source": f"doc_{i}"}],
            ids=[str(i)]
        )

    print("RAG KB created with", len(chunked_docs), "chunks.")
    return collection
