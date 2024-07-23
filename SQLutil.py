import os

from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from operator import itemgetter

from flask import Flask, request, jsonify

app = Flask(__name__)

llm = ChatGoogleGenerativeAI(model="gemini-pro",temperature=0)

from langfuse.callback import CallbackHandler
langfuse_handler = CallbackHandler(
    secret_key=os.getenv('langfuse_secret_key'),
    public_key=os.getenv('langfuse_public_key'),
    host=os.getenv('langfuse_host'), 
)

sql_prompt=PromptTemplate.from_template(
    '''Given an input question and previous messages for context first create a syntactically correct {dialect} query to run. Do not put the query you make in markdowns as sql, keep it as simple text. Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per SQLite.

    Question: {input}
    Message history:
    {message_history}
    
    Only use the following tables:
    {table_info}

    SQLQuery:'''
)

answer_prompt = PromptTemplate.from_template(
    """Given the following user question, previous messages for context, corresponding SQL query, and SQL result, answer the user question.

    Question: {question}
    Message History:{message_history}
    SQL Query: {query}
    SQL Result: {result}
    Answer: """
)

def get_chain(dbinfo):
    db_uri = f"mysql+pymysql://{dbinfo['user']}:{dbinfo['password']}@{dbinfo['host']}:{dbinfo['port']}/{dbinfo['database']}"
    db= SQLDatabase.from_uri(db_uri)
    print(db.get_usable_table_names())
    SQLChain = create_sql_query_chain(llm, db,prompt=sql_prompt)
    execute_query = QuerySQLDataBaseTool(db=db)
    rephrase_answer = answer_prompt | llm | StrOutputParser()
    chain = (
        RunnablePassthrough.assign(query=SQLChain).assign(
            result=itemgetter("query") | execute_query
        )
        | rephrase_answer
    )
    return chain

def invoke_chain(question,history,dbinfo):
    chain = get_chain(dbinfo)
    response = chain.invoke({"question": question,"message_history":history})
    print(response)
    return response

@app.route('/invoke', methods=['POST'])
def invoke():
    data = request.get_json()
    question = data.get('question')
    history = data.get('history')
    dbinfo = data.get('dbinfo')
    
    if not question or not history or not dbinfo:
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        response = invoke_chain(question, history, dbinfo)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
    
    
