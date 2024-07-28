from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import os

def process_texts(files):
    texts = []
    for file in files:
        file_content = file.read().decode('utf-8')
        text = Document(page_content=file_content)
        texts.append(text)
    combined_text = "\n\n".join(text.page_content for text in texts)
    return combined_text, texts

def chat_with_text_files(query, texts):
    if not texts:
        return "No texts available for processing."

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150, add_start_index=True)
    docs_split = text_splitter.split_documents(texts)

    if not docs_split:
        return "Text splitting resulted in no documents."

    # Define embedding
    embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    # Check if the embedding can be created successfully
    try:
        # Create vector database from data    
        db = FAISS.from_documents(docs_split, embedding=embedding)
    except IndexError:
        return "Error creating embeddings from the provided documents."

    # Initialize the LLM
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3, api_key=os.getenv("GOOGLE_API_KEY"))
    
    # Define prompt template
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    
    # QA CHAIN
    qa_chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt)
    
    # Run QA chain
    docs = db.similarity_search(query)
    if not docs:
        return "No similar documents found for the given query."
    
    response = qa_chain.run(input_documents=docs, question=query)
    return response
