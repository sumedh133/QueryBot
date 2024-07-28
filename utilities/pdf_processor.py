from langchain.schema import Document
from PyPDF2 import PdfReader

def process_pdfs(files):
    texts = []
    for file in files:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        texts.append(Document(page_content=text))
    combined_text = "\n\n".join(text.page_content for text in texts)
    return combined_text, texts
