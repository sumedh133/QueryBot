import os
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import ast
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from operator import itemgetter

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
    """Given the following user question, previous messages for context, corresponding SQL query, and SQL result, answer the user question.If the result from the database is a big table and is itself the answer no need to rephrase it or say it again.

    Question: {question}
    Message History:{message_history}
    SQL Query: {query}
    SQL Result: {result}
    Answer: """
)

def get_chain(db):
    SQLChain = create_sql_query_chain(llm, db, prompt=sql_prompt)
    execute_query = QuerySQLDataBaseTool(db=db)
    
    chain = RunnablePassthrough.assign(
        query=SQLChain
    ).assign(
        result=itemgetter("query") | execute_query
    ).assign(
        rephrasedAnswer= answer_prompt | llm | StrOutputParser()
    )

    return chain

def invoke_chain(question,history,db):
    chain = get_chain(db)
    response = chain.invoke({"question": question,"message_history":history})
    result_list = ast.literal_eval(response['result'])
    response['result']=pd.DataFrame(result_list)
    return response