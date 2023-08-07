"""
This is a Python script that serves as a frontend for a conversational AI model built with the `langchain` and `llms` libraries.
The code creates a web application using Streamlit, a Python library for building interactive web apps.
# Author: Dorsa Rohani
# Date: AUgust 04, 2023
"""


# Import necessary libraries
import os 
import openai

from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.llms import OpenAI
from langchain.vectorstores import Chroma

import streamlit as st 
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain 
from langchain.memory import ConversationBufferMemory
from langchain.utilities import WikipediaAPIWrapper 

from pdfreader import PDFDocument, SimplePDFViewer

from key import APIKEY #import api key from key.py
os.environ['OPENAI_API_KEY'] = APIKEY



# Set Streamlit page configuration
st.set_page_config(page_title='🧠 CustomAI', layout='wide')


# Side bar api key
openai_api_key = st.sidebar.text_input('OpenAI API Key')
st.sidebar.markdown("*Please enter your OpenAI API key*")

st.write("#")
st.sidebar.title(":blue[CustomAI]")
st.sidebar.markdown("Train AI with custom data, revolutionizing personalized AI. Here are sample use cases:")

# RealizeAI
st.sidebar.subheader(":blue[1. [RealizeAI](https://realize-ai.com/)]")
st.sidebar.markdown("*Think your unique knowledge has no real-world value?*")
st.sidebar.markdown("*http://realize-ai.com/*")
# PatientGPT.AI
st.sidebar.subheader(":blue[2. [PatientGPT.AI](https://realize-ai.com/)]")
st.sidebar.markdown("*Think your unique knowledge has no real-world value?*")
st.sidebar.markdown("*[Github - PatientGPT.AI](https://github.com/DorsaRoh/Custom-AI/tree/main/Sample%20Use%20-%20PatientGPT.AI)*")

# Sample use cases



 #If invalid/no api key enteblue, show warning
def valid_apikey():
    if openai_api_key.startswith('sk-'):
        return True
    else:
        st.warning('Invalid API Key', icon='⚠')
        return False


# Title
st.title('Custom-AI')
st.subheader(':blue[Train AI on *your* custom data.]')
st.write("#")

if valid_apikey():
    st.success('Valid API Key', icon='✅')

# Enable to save to disk & reuse the model (for repeated queries on the same data)
PERSIST = False

# Langchain LLM that feeds off of user data
def load_model():
    if PERSIST and os.path.exists("persist"):
        st.write("Reusing index...\n")
        vectorstore = Chroma(persist_directory="persist", embedding_function=OpenAIEmbeddings())
        index = VectorStoreIndexWrapper(vectorstore=vectorstore)
    else:
        loader = DirectoryLoader("data/")
        if PERSIST:
            index = VectorstoreIndexCreator(vectorstore_kwargs={"persist_directory":"persist"}).from_loaders([loader])
        else:
            index = VectorstoreIndexCreator().from_loaders([loader])
    
    chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(model="gpt-3.5-turbo"),
        retriever=index.vectorstore.as_retriever(search_kwargs={"k": 1}),
    )

    return chain

chain = load_model()
chat_history = []



# FILE SAVE TO DATA FOLDER

# Extract text from user uploaded pdf file - so LLM can read it
def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as fd:
        viewer = SimplePDFViewer(fd)
        text = ""
        for page in viewer:
            viewer.render()
            text += ' '.join(viewer.canvas.strings)
    return text

def fileSaver():
    #st.title("File Uploader and Saver")
    uploaded_file = st.file_uploader("Input data", type='.pdf')

    if uploaded_file is not None and valid_apikey():
        with open(os.path.join("data", uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("File has been saved successfully!")

        # create a text file with the pdf's text content
        file_path = os.path.join("data", uploaded_file.name)
        text_content = extract_text_from_pdf(file_path)
        with open(os.path.splitext(file_path)[0]+".txt", "w") as f: 
            f.write(text_content)

fileSaver()


# Prompt templates for Langchain
class PromptTemplate:
    def __init__(self, input_variables, template):
        self.input_variables = input_variables
        self.template = template

    def format(self, **kwargs):
        # Check if all necessary variables have been provided
        for variable in self.input_variables:
            if variable not in kwargs:
                raise ValueError(f"Missing input variable: {variable}")

        # Use the provided variables to format the template
        return self.template.format(**kwargs)

title_template = PromptTemplate(
    input_variables=['topic'], 
    template='Answer with the best possible answer to {topic} using data'
)

script_template = PromptTemplate(
    input_variables=['title', 'wikipedia_research'], 
    template=(
        "ChatGPT, considering your last update in September 2021 and leveraging all the information you have up to that point, provide a detailed and evidence-based answer on {title}. Please be specific, cite any relevant information, and leverage {wikipedia_research}"
    )
)


chain = load_model()
diagnosis = st.text_input("Ask AI:")
wiki = WikipediaAPIWrapper()

if diagnosis and valid_apikey():
    try:
        title_prompt = title_template.format(topic=diagnosis)
        title_result = chain({"question": title_prompt, "chat_history": chat_history})
        chat_history.append((title_prompt, title_result['answer']))

        wiki = WikipediaAPIWrapper()
        wiki_research = wiki.run(diagnosis) 

        script_prompt = script_template.format(title=diagnosis, wikipedia_research=wiki_research)

        script_result = chain({"question": script_prompt, "chat_history": chat_history})
        st.write(f"AI: {script_result['answer']}")
        chat_history.append((script_prompt, script_result['answer']))
    except TypeError as e:
        st.write("An error occurblue: ", e)



# ADDITIONAL QUESTIONS

def generate_questions_response(input_text):
    chain = load_model()
    chat_history = []

    query = input_text

    if query not in ['', 'quit', 'q', 'exit']:
        result = chain({"question": query, "chat_history": chat_history})
        st.write(f"AI: {result['answer']}")
        chat_history.append((query, result['answer']))

with st.form('additional_questions_form'):
    query = st.text_area('Enter additional questions and/or notes:', '...')    
    submitted = st.form_submit_button(label='Submit')
    valid_apikey()
    if submitted and valid_apikey():
        generate_questions_response(query)



