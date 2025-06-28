import os
import pinecone
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
import streamlit as st

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override = True)

index_name = 'askadocument'
embeddings = OpenAIEmbeddings()
pinecone.init(api_key=os.environ.get('PINECONE_API_KEY'), environment=os.environ.get('PINECONE_ENV'))

def ask_and_get_answer(vector_store, q):
    from langchain.chains import RetrievalQA
    from langchain.chat_models import ChatOpenAI

    llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=1)

    retriever = vector_store.as_retriever(search_type='similarity', search_kwargs={'k': 3})

    chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
    
    answer = chain.run(q)
    return answer
    
    
def ask_with_memory(vector_store, question, chat_history=[]):
    from langchain.chains import ConversationalRetrievalChain
    from langchain.chat_models import ChatOpenAI
    
    llm = ChatOpenAI(temperature=1)
    retriever = vector_store.as_retriever(search_type='similarity', search_kwargs={'k': 3})
    
    crc = ConversationalRetrievalChain.from_llm(llm, retriever)
    result = crc({'question': question, 'chat_history': chat_history})
    chat_history.append((question, result['answer']))
    
    return result, chat_history

vector_store = Pinecone.from_existing_index(index_name, embeddings)

st.title('Smithsonian Institution')
prompt = st.text_input('Ask SmithAI')

if prompt:
    # Then pass the prompt to the LLM
    response = ask_and_get_answer(vector_store, prompt)
    # ...and write it out to the screen
    st.write(response)
