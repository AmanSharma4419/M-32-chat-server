from langchain.tools import tool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import ChatOpenAI
import os
from app.db.mongo import sessions_collection

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    api_key=OPENAI_API_KEY
)


@tool("pdf_qa")
def pdf_qa_tool(question: str) -> str:
    """
    Answer a question based on the uploaded PDF content. Use this for
    questions about uploaded documents, resumes, or PDF content.
    The tool automatically retrieves the PDF content from the current session.
    """
    try:
        return "PDF tool is currently unavailable. Please try again later."

    except Exception as e:
        return f"Error processing your PDF question: {str(e)}"


class PDFQATool:
    def __init__(self, session_id):
        self.session_id = session_id

    async def run(self, question: str) -> str:
        """Run the PDF QA tool with the stored session_id"""
        try:
            session = await sessions_collection.find_one({"session_id": self.session_id})
            if not session or not session.get("pdf") or not session["pdf"].get("content"):
                return "No PDF content available. Please upload a PDF first."

            pdf_content = session["pdf"]["content"]

            if not pdf_content or pdf_content.strip() == "":
                return "No PDF content available. Please upload a PDF first."

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=50
            )
            chunks = splitter.split_text(pdf_content)

            if not chunks:
                return "PDF content is empty or could not be processed."

            embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
            vector_store = FAISS.from_texts(chunks, embeddings)

            if any(keyword in question.lower() for keyword in ['skill', 'technology', 'programming', 'language', 'tool']):
                search_query = "skills technologies programming languages tools frameworks experience"
            elif any(keyword in question.lower() for keyword in ['experience', 'job', 'work', 'position']):
                search_query = "experience work job position employment history"
            elif any(keyword in question.lower() for keyword in ['education', 'degree', 'school', 'university']):
                search_query = "education degree school university college qualification"
            else:
                search_query = question

            relevant_docs = vector_store.similarity_search(search_query, k=4)

            if not relevant_docs:
                return "I couldn't find relevant information in the PDF to answer your question."

            qa_chain = load_qa_chain(llm, chain_type="stuff")
            answer = qa_chain.run(
                input_documents=relevant_docs, question=question)

            return answer

        except Exception as e:
            return f"Error processing your PDF question: {str(e)}"
