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

def init_database(user: str, password: str, host: str, port: str, database: str) -> SQLDatabase:
    db_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    return SQLDatabase.from_uri(db_uri)

# Extract URL parameters
query_params = st.experimental_get_query_params()
conversation_id = query_params.get("conversation_id", [None])[0]

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "db" not in st.session_state:
    st.session_state.db = None

# Load conversation if conversation_id is provided
if conversation_id:
    conversation = conversations_collection.find_one({"_id": ObjectId(conversation_id)})
    if conversation:
        # Load existing chat history
        if "messages" in conversation:
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
            st.session_state.db = init_database(user, password, host, port, database)
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

# Display chat history
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        try:
            ai_content = json.loads(message.content)
            with st.chat_message("AI"):
                st.markdown(f"🟢 **Query:** {ai_content.get('query', 'N/A')}")
                st.markdown(f"🟢 **Result:**")
                if isinstance(ai_content.get('result'), str):
                    st.text(ai_content['result'])
                else:
                    st.dataframe(pd.DataFrame(ai_content['result']))
                st.markdown(f"💡 **Rephrased Answer:** {ai_content.get('rephrasedAnswer', '')}")
        except json.JSONDecodeError:
            # Fallback for older messages
            with st.chat_message("AI"):
                st.markdown(f"🟢 {message.content}")
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
    with st.chat_message("Human"):
        st.markdown(f"✍️ {user_query}")

    with st.chat_message("AI"):
        if user_query.lower() in specific_words_responses:
            response = specific_words_responses[user_query.lower()]
            response_text = response
            query_text = "N/A"
            rephrased_answer = response
            result = response
        else:
            response = st.session_state.chain.invoke_chain(user_query, st.session_state.chat_history)
            query_text = response['query']
            rephrased_answer = response['rephrasedAnswer']
            if isinstance(response['result'], pd.DataFrame):
                result = response['result'].to_dict()
            else:
                result = response['result']
            response_text = f"```sql\n{response['query']}\n```\n"
            response_text += f"{result}\n"
            response_text += f"💡 {response['rephrasedAnswer']}"

        st.markdown(f"**Query:** {query_text}")
        st.markdown(f"**Result:**")
        if isinstance(result, str):
            st.text(result)
        else:
            st.dataframe(pd.DataFrame(result))
        st.markdown(f"💡 {rephrased_answer}")

    # Append messages to chat history
    st.session_state.chat_history.append(HumanMessage(content=user_query))
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
