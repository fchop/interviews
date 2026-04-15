import os
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate


# --- Constants ---
PDF_DIR = "app\static"  # Adjust path if needed
INDEX_DIR = os.path.join("app", "static", "faiss_index")
PDF_FILES = ["Handbook Volume 1.pdf", "Handbook Volume 2.pdf", "ODI evidence of cash transfers.pdf"]  # Your documents
CHUNK_SIZE = 800  # Adjust chunk size as needed
CHUNK_OVERLAP = 200

# --- Get openai api key ---
load_dotenv()  # This reads from the .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Load PDFs ---
def load_documents():
    docs = []
    for pdf in PDF_FILES:
        path = os.path.join(PDF_DIR, pdf)
        loader = PyPDFLoader(path)
        docs.extend(loader.load())
    return docs

def create_vectorstore():
    """Split, embed, and save documents to FAISS index."""
    print("Creating FAISS index from scratch...")
    docs = load_documents()
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings()
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(INDEX_DIR)
    return db

def get_vectorstore():
    """Load FAISS vectorstore if exists, otherwise create it."""
    embeddings = OpenAIEmbeddings()
    if os.path.exists(INDEX_DIR):
        return FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
    return create_vectorstore()

def get_qa_chain():
    """Return a RetrievalQA chain using the vectorstore."""
    retriever = get_vectorstore().as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": 0.6, "k": 5} 
    )

    # Custom prompt to reduce references to "the text"
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template=(
            "You are a helpful assistant answering questions based on a policy handbook."
            " Use the context below to answer the question clearly and concisely."
            " Simplify any complex language and avoid jargon."
            " Talk in layman's terms and make it easy to understand."
            " Do not mention 'the text' or that you're referencing any document."
            " If the context is insufficient, say you don't have enough information.\n\n"
            "Context:\n{context}\n\n"
            "Question: {question}\n"
            "Answer:"
        )
    )

    return RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.5),
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt_template},
    )