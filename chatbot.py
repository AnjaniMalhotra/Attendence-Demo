import streamlit as st
import pandas as pd
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents.agent_types import AgentType # To specify the agent type
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder # For custom prompt

# Function to initialize and return the Gemini-powered Pandas DataFrame agent
def get_gemini_pandas_agent(df: pd.DataFrame):
    """
    Initializes and returns a LangChain Pandas DataFrame agent powered by Google Gemini.

    Args:
        df (pd.DataFrame): The Pandas DataFrame that the agent will query.

    Returns:
        AgentExecutor: A LangChain agent configured to answer questions about the DataFrame.
    """
    # Ensure the Google API key is available in Streamlit secrets
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("Google API Key not found in .streamlit/secrets.toml. Please add it.")
        st.stop() # Stop the app if the key is missing

    # Initialize the Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=st.secrets["GOOGLE_API_KEY"],
        temperature=0.2 # Increased temperature slightly for more robust generation
    )

    # Define a custom prompt to guide the agent, ensuring it always provides a concrete answer
    # This helps prevent empty responses from the LLM.
    system_message = (
        "You are an AI assistant specialized in analyzing attendance data. "
        "Your goal is to answer questions about the provided Pandas DataFrame. "
        "Always provide a clear and concise answer. If you cannot find a direct answer, "
        "state that clearly rather than returning an empty response. "
        "The DataFrame contains 'Roll Number', 'Name', and date columns (e.g., 'YYYY-MM-DD') "
        "where 'P' indicates present and empty/NaN indicates absent."
    )

    # Create the Pandas DataFrame agent
    agent = create_pandas_dataframe_agent(
        llm,
        df,
        verbose=True,
        agent_type=AgentType.OPENAI_FUNCTIONS, # This agent type is generally robust
        handle_parsing_errors=True,
        allow_dangerous_code=True,
        # Add a system message to the agent's prompt
        agent_executor_kwargs={"handle_parsing_errors": True}, # Ensure parsing errors are handled
        agent_kwargs={"system_message": system_message}
    )
    return agent
