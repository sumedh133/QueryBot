import os
from dotenv import load_dotenv, find_dotenv
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

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

llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)

from langfuse.callback import CallbackHandler
langfuse_handler = CallbackHandler(
    secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
    public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
    host=os.getenv('LANGFUSE_HOST'), 
)

sql_prompt = PromptTemplate.from_template(
    '''Given an input question/query/instruction and previous messages for context first create a syntactically correct {dialect} query to run. Do not put the query you make in markdowns as sql, keep it as simple text. Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per {dialect}.

    Question: {input}
    Message history:
    {message_history}
    
    Only use the following tables:
    {table_info}'''
)

answer_prompt = PromptTemplate.from_template(
    """Given the following user question, previous messages for context, corresponding SQL query, and SQL result, answer the user question. If the SQL result is blank then the query returned nothing. If the SQL result is a table then dont use that table again in the answer you give.
    
    Question: {question}
    Message History:{message_history}
    SQL Query: {query}
    SQL Result: {result}"""
)

class SQLChain:
    def __init__(self, db):
        self.db = db
        self.chain = self.create_chain()

    def create_chain(self):
        SQLChain = create_sql_query_chain(llm, self.db, prompt=sql_prompt)
        execute_query = QuerySQLDataBaseTool(db=self.db)
        
        chain = RunnablePassthrough.assign(
            query=SQLChain
        ).assign(
            result=itemgetter("query") | execute_query
        ).assign(
            rephrasedAnswer= answer_prompt | llm | StrOutputParser()
        )

        return chain


    def invoke_chain(self, question, history):
        response = self.chain.invoke({"question": question, "message_history": history,"top_k":10},config={"callbacks": [langfuse_handler]})
        try:
            if response['result'].strip():  
                result_list = ast.literal_eval(response['result'])
                response['result'] = pd.DataFrame(result_list)
        except (ValueError, SyntaxError) as e:
            print(f"Error converting result to DataFrame: {e}")
        
        return response
