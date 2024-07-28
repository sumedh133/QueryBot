from langchain.schema import Document
from PyPDF2 import PdfReader
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings

def process_pdfs(files):
    """
    Process PDF files and convert their content to a single text string and a list of Document objects.

    Parameters:
    - files (list): List of uploaded PDF files.

    Returns:
    - combined_text (str): Combined text content of all PDF files.
    - texts (list): List of Document objects containing text for each PDF.
    """
    texts = []
    for file in files:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        texts.append(Document(page_content=text))
    combined_text = "\n\n".join(text.page_content for text in texts)
    return combined_text, texts

def create_faiss_index(documents):
    """
    Create a FAISS index from a list of documents.

    Parameters:
    - documents (list): List of Document objects.

    Returns:
    - index: The created FAISS index.
    """
    # Initialize the embeddings
    embeddings = OpenAIEmbeddings()

    # Create the FAISS index
    index = FAISS.from_documents(documents, embeddings)
    
    return index

def search_faiss_index(index, query):
    """
    Search a FAISS index with a query.

    Parameters:
    - index: The FAISS index to search.
    - query (str): The query to search with.

    Returns:
    - results (list): List of search results.
    """
    # Perform the search
    results = index.search(query)
    
    return results
