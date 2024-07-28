from dotenv import load_dotenv, find_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.utilities import SQLDatabase
import streamlit as st
import pandas as pd
import pymongo
from bson import ObjectId
import os
import json
from utilities.SQL import SQLChain

# Load environment variables
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

# MongoDB connection
client = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DB_NAME")]
conversations_collection = db["conversations"]

# Page configuration
st.set_page_config(page_title="Chat with QueryBot", page_icon=":speech_balloon:", layout="wide")

def message_to_dict(message):
    return {
        "role": "AI" if isinstance(message, AIMessage) else "Human",
        "content": message.content
    }

def init_database(db_type: str, user: str, password: str, host: str, port: str, database: str) -> SQLDatabase:
    if db_type == 'MySQL':
        db_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    elif db_type == 'PostgreSQL':
        db_uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    elif db_type == 'SQLite':
        db_uri = f"sqlite:///{database}"
    elif db_type == 'SQLServer':
        db_uri = f"mssql+pyodbc://{user}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
    else:
        raise ValueError("Unsupported database type")
    return SQLDatabase.from_uri(db_uri)

# Extract URL parameters
conversation_id = st.query_params.to_dict()['conversation_id']

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "db" not in st.session_state:
    st.session_state.db = None
    
st.button("⚙️ Settings")


# Load conversation if conversation_id is provided
if conversation_id:
    conversation = conversations_collection.find_one({"_id": ObjectId(conversation_id)})
    if conversation:
        # Load existing chat history
        if "messages" in conversation:
            st.session_state.chat_history = []
            for msg in conversation["messages"]:
                if msg["role"] == "AI":
                    st.session_state.chat_history.append(AIMessage(content=msg["content"]))
                else:
                    st.session_state.chat_history.append(HumanMessage(content=msg["content"]))

        db_type = conversation["db_type"]
        host = conversation["host"]
        port = conversation["port"]
        user = conversation["user"]
        password = conversation["password"]
        database = conversation["database"]

        # Initialize the database connection
        try:
            st.session_state.db = init_database(db_type, user, password, host, port, database)
            if st.session_state.db.get_usable_table_names():
                st.success("Connected to database!")
                st.session_state.chain = SQLChain(st.session_state.db)
        except Exception as e:
            st.error('An error occurred. Check database connection and credentials')
            print(e)
    else:
        st.error("Invalid conversation ID.")
else:
    st.error("No conversation ID provided in URL.")

# Main Title
st.title("💬 Chat with QueryBot")

# Sidebar for database information
with st.sidebar:
    st.header("Database Information")
    if conversation_id:
        st.write(f"**Database Type:** {db_type}")
        st.write(f"**Host:** {host}")
        st.write(f"**Port:** {port}")
        st.write(f"**User:** {user}")
        st.write(f"**Database:** {database}")
    else:
        st.write("No database information available")

# Display chat history
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        try:
            ai_content = json.loads(message.content)
            with st.chat_message("AI"):
                if ai_content.get('query') and ai_content.get('query') != 'N/A':
                    st.markdown(f"```sql\n{ai_content.get('query')}\n```")
                if ai_content.get('result'):
                    if isinstance(ai_content.get('result'), str):
                        st.text(ai_content['result'])
                    else:
                        st.dataframe(pd.DataFrame(ai_content['result']))
                st.markdown(f"💡 {ai_content.get('rephrasedAnswer', '')}")
        except json.JSONDecodeError:
            # Fallback for older messages
            with st.chat_message("AI"):
                st.markdown(f"💡 {message.content}")
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(f"✍️ {message.content}")

# Define a list of specific words and their responses
specific_words_responses = {
    "ok": "Got it! Anything else I can help with?",
    "thank you": "You're welcome! Happy to assist.",
    "alright": "Okay, let me know if there's anything else.",
    # Add more words and responses as needed
}

user_query = st.chat_input("Type a message...")
if user_query:
    # Append the user message to chat history
    st.session_state.chat_history.append(HumanMessage(content=user_query))

    with st.chat_message("Human"):
        st.markdown(f"✍️ {user_query}")

    response = None
    with st.chat_message("AI"):
        if user_query.lower() in specific_words_responses:
            response = specific_words_responses[user_query.lower()]
            query_text = "N/A"
            rephrased_answer = response
            result = None
        else:
            response = st.session_state.chain.invoke_chain(user_query, st.session_state.chat_history)
            query_text = response['query']
            rephrased_answer = response['rephrasedAnswer']
            if isinstance(response['result'], pd.DataFrame):
                result = response['result'].to_dict()
            else:
                result = response['result']
        
        if query_text and query_text != 'N/A':
            st.markdown(f"```sql\n{query_text}\n```")
        if result:
            if isinstance(result, str):
                st.text(result)
            else:
                st.dataframe(pd.DataFrame(result))
        st.markdown(f"💡 {rephrased_answer}")

        # Append the AI response to chat history
        ai_message_content = {
            "query": query_text,
            "result": result,
            "rephrasedAnswer": rephrased_answer
        }
        st.session_state.chat_history.append(AIMessage(content=json.dumps(ai_message_content)))

    # Store chat history in MongoDB
    conversations_collection.update_one(
        {"_id": ObjectId(conversation_id)},
        {"$set": {"messages": [message_to_dict(msg) for msg in st.session_state.chat_history]}}
    )
