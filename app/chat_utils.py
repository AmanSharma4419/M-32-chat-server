import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from langchain.agents import initialize_agent, AgentType
from app.db.mongo import sessions_collection

# All tools available
from app.tools.research_tool import research_papers
from app.tools.web_search_tool import web_search
from app.tools.pdf_tool import PDFQATool

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Chat LLM Openai
chat_model = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    api_key=OPENAI_API_KEY
)

tools = [research_papers, web_search]


async def get_bot_response(user_id: str, session_id: str, user_input: str):
    """
    Main function to get chatbot response.
    Integrates PDF QA, research papers, web search, and conversation memory.
    """
    # Initialize  memory
    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True
    )

    session = await sessions_collection.find_one({"session_id": session_id})
    user_facts = ""
    pdf_content = None

    if session:
        restored_messages = []
        for msg in session.get("messages", []):
            if msg["type"] == "human":
                restored_messages.append(HumanMessage(content=msg["content"]))
            elif msg["type"] == "ai":
                restored_messages.append(AIMessage(content=msg["content"]))
        memory.chat_memory.messages = restored_messages

        user_facts = session.get("user_facts", "")
        if user_facts:
            memory.chat_memory.add_message(
                AIMessage(
                    content=f"Remember this user information: {user_facts}")
            )

        if session.get("pdf") and session["pdf"].get("content"):
            pdf_content = session["pdf"]["content"]
            memory.chat_memory.add_message(
                AIMessage(
                    content="User has uploaded a PDF document available for questioning.")
            )

    if "my name is" in user_input.lower():
        name = user_input.split("is")[-1].strip()
        user_facts = f"My name is {name}"

    # Check if this is a PDF-related question
    is_pdf_question = (
        pdf_content and
        (
            "pdf" in user_input.lower() or
            "document" in user_input.lower() or
            "resume" in user_input.lower() or
            "cv" in user_input.lower() or
            "upload" in user_input.lower() or
            any(word in user_input.lower() for word in ['my', 'me', 'i']) and
            any(word in user_input.lower()
                for word in ['skill', 'experience', 'education', 'work', 'job'])
        )
    )

    try:
        if is_pdf_question:
            pdf_tool = PDFQATool(session_id)
            result_text = await pdf_tool.run(user_input)
            result_text = f"Based on your uploaded document:\n{result_text}"
        else:
            agent_executor = initialize_agent(
                tools=tools,
                llm=chat_model,
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                memory=memory,
                verbose=False,
                handle_parsing_errors=True
            )
            result_text = agent_executor.run(user_input)

    except Exception as e:
        result_text = f"I encountered an error while processing your request: {str(e)}. Please try again."

    messages_to_save = []
    for msg in memory.chat_memory.messages:
        if isinstance(msg, HumanMessage):
            messages_to_save.append({"type": "human", "content": msg.content})
        elif isinstance(msg, AIMessage):
            messages_to_save.append({"type": "ai", "content": msg.content})

    update_data = {
        "user_id": user_id,
        "messages": messages_to_save,
        "user_facts": user_facts,
        "updated_at": datetime.utcnow()
    }

    if session and session.get("pdf"):
        update_data["pdf"] = session["pdf"]

    await sessions_collection.update_one(
        {"session_id": session_id},
        {"$set": update_data},
        upsert=True
    )

    return result_text
