from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.utilities import SQLDatabase
import streamlit as st 
import requests

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

st.set_page_config(page_title="Chat with QueryBot", page_icon=":speech_balloon:", layout="wide")

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
    db_type = st.sidebar.selectbox("Database Type", ["Select a database", "MySQL","MongoDB", "CSV", "Excel", "PDF", "Word", "TXT"])

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
                    db = init_database(
                        st.session_state["User"],
                        st.session_state["Password"],
                        st.session_state["Host"],
                        st.session_state["Port"],
                        st.session_state["Database"]
                    )
                    if(db.get_usable_table_names()):
                        st.success("Connected to database!")   
                        st.session_state.db = db 
                except Exception as e:
                    st.error('An error occured. Check database connection and credentials')
                    print(e)
    elif db_type == "MongoDB":
        st.sidebar.text_input("Host", value="localhost", key="Mongo_Host")
        st.sidebar.text_input("Port", value="27017", key="Mongo_Port")
        st.sidebar.text_input("User", value="admin", key="Mongo_User")
        st.sidebar.text_input("Password", type="password", value="passcode", key="Mongo_Password")
        st.sidebar.text_input("Database", value="ClientData", key="Mongo_Database")
        if st.sidebar.button("Connect"):
            with st.spinner("Connecting to database..."):
                db = init_mongo_database(
                    st.session_state["Mongo_User"],
                    st.session_state["Mongo_Password"],
                    st.session_state["Mongo_Host"],
                    st.session_state["Mongo_Port"],
                    st.session_state["Mongo_Database"]
                )
                st.session_state.db = db
                st.success("Connected to database!")

    elif db_type == "CSV":
        csv_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
        if csv_file is not None:
            with st.spinner("Loading CSV file..."):
                df = load_csv(csv_file)
                st.session_state.df = df
                st.success("CSV file loaded!")

    elif db_type == "Excel":
        excel_file = st.sidebar.file_uploader("Upload Excel file", type=["xls", "xlsx"])
        if excel_file is not None:
            with st.spinner("Loading Excel file..."):
                df = load_excel(excel_file)
                st.session_state.df = df
                st.success("Excel file loaded!")

    elif db_type == "PDF":
        pdf_file = st.sidebar.file_uploader("Upload PDF file", type=["pdf"])
        if pdf_file is not None:
            with st.spinner("Loading PDF file..."):
                text = load_pdf(pdf_file)
                st.session_state.text = text
                st.success("PDF file loaded!")

    elif db_type == "Word":
        word_file = st.sidebar.file_uploader("Upload Word file", type=["doc", "docx"])
        if word_file is not None:
            with st.spinner("Loading Word file..."):
                text = load_word(word_file)
                st.session_state.text = text
                st.success("Word file loaded!")

    elif db_type == "TXT":
        txt_file = st.sidebar.file_uploader("Upload TXT file", type=["txt"])
        if txt_file is not None:
            with st.spinner("Loading TXT file..."):
                text = load_txt(txt_file)
                st.session_state.text = text
                st.success("TXT file loaded!")


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
            payload = {
                "question": user_query,
                "history": [message_to_dict(message) for message in st.session_state.chat_history],
                "dbinfo": {
                    "type": db_type,
                    "host": st.session_state["Host"],
                    "port": st.session_state["Port"],
                    "user": st.session_state["User"],
                    "password": st.session_state["Password"],
                    "database": st.session_state["Database"]
                }  
            }
            try:
                res = requests.post("http://127.0.0.1:5000/invoke", json=payload)
                res.raise_for_status()
                response = res.json().get("response", "Sorry, I didn't understand that.")
            except requests.exceptions.RequestException as e:
                print(e)
                response = f"API request failed: {e}"
        
        st.markdown(f"💡 {response}")
    st.session_state.chat_history.append(HumanMessage(content=user_query))
    st.session_state.chat_history.append(AIMessage(content=response))