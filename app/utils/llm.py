# Import the os module so we can read values from the operating system environment
import os

# Import load_dotenv so Python can load variables from the .env file
from dotenv import load_dotenv

# Import ChatGroq, which is the LangChain class used to call Groq chat models
from langchain_groq import ChatGroq

# Import message classes used by LangChain chat models
from langchain_core.messages import HumanMessage, SystemMessage


# Load environment variables from the .env file into Python
load_dotenv()


# Create a function that returns a Groq LLM object
def get_llm(temperature: float = 0.2) -> ChatGroq:
    # Read the Groq API key from the .env file
    api_key = os.getenv("GROQ_API_KEY")

    # Read the model name from the .env file
    model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # Check whether the API key is missing
    if not api_key:
        # Stop the program and show a clear error message
        raise ValueError(
            "GROQ_API_KEY is missing. Please add your Groq API key to the .env file."
        )

    # Create the LangChain Groq chat model object
    llm = ChatGroq(
        # Select the Groq model name
        model=model_name,

        # Set the creativity level of the model
        temperature=temperature,

        # Pass the Groq API key to the model
        api_key=api_key,
    )

    # Return the LLM object so other files can use it
    return llm


# Create a simple helper function to call the LLM
def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    # Create the Groq LLM object using the function above
    llm = get_llm(temperature=temperature)

    # Create the system message, which tells the model how it should behave
    system_message = SystemMessage(content=system_prompt)

    # Create the human message, which contains the user question or task
    human_message = HumanMessage(content=user_prompt)

    # Put both messages into a list in the correct order
    messages = [system_message, human_message]

    # Send the messages to the Groq model using LangChain
    response = llm.invoke(messages)

    # Return only the text content from the model response
    return response.content