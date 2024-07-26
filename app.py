from dotenv import load_dotenv,find_dotenv
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.utilities import SQLDatabase
import streamlit as st 
import os

from utilities.SQL import invoke_chain

st.set_page_config(page_title="Chat with QueryBot", page_icon=":speech_balloon:", layout="wide")

    
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Hello! I'm your assistant named QueryBot. Click on the settings icon then connect to the database and start chatting."),
    ]

if "db" not in st.session_state:
    st.session_state.db=None
    
def message_to_dict(message):
    return {
        "role": "AI" if isinstance(message, AIMessage) else "Human",
        "content": message.content
    }


def init_database(user: str, password: str, host: str, port: str, database: str) -> SQLDatabase:
    db_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    return SQLDatabase.from_uri(db_uri)


# Toggle sidebar visibility
if 'show_settings' not in st.session_state:
    st.session_state.show_settings = False

# Use a button with an emoji as a settings icon
if st.button("⚙️ Settings"):
    st.session_state.show_settings = not st.session_state.show_settings

# Sidebar
if st.session_state.show_settings:
    st.sidebar.subheader("Settings")
    st.sidebar.write("This is a chat application. Select a database type, connect, and start chatting.")

    # Dropdown for selecting database type
    db_type = st.sidebar.selectbox("Database Type", ["Select a database", "MySQL"])

    # Display connection fields based on selected database type
    if db_type == "MySQL":
        st.sidebar.text_input("Host", value="localhost", key="Host")
        st.sidebar.text_input("Port", value="3306", key="Port")
        st.sidebar.text_input("User", value="root", key="User")
        st.sidebar.text_input("Password", type="password", value="ssb13032004", key="Password")
        st.sidebar.text_input("Database", value="classicmodels", key="Database")
        if st.sidebar.button("Connect"):
            with st.spinner("Connecting to database..."):
                try:
                    st.session_state.db = init_database(
                        st.session_state["User"],
                        st.session_state["Password"],
                        st.session_state["Host"],
                        st.session_state["Port"],
                        st.session_state["Database"]
                    )
                    if(st.session_state.db.get_usable_table_names()):
                        st.success("Connected to database!")   
                except Exception as e:
                    st.error('An error occured. Check database connection and credentials')
                    print(e)


# Main Title
st.title("💬 Chat with QueryBot")  
# Display chat history
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
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
        else:
            response=invoke_chain(user_query,st.session_state.chat_history,st.session_state.db)
            
        st.markdown(f"```sql\n{response['query']}\n```")
        st.dataframe(response['result'])
        st.markdown(f"💡 {response['rephrasedAnswer']}")
    st.session_state.chat_history.append(HumanMessage(content=user_query))
    st.session_state.chat_history.append(AIMessage(content=response['rephrasedAnswer']))