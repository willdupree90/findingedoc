from dotenv import load_dotenv
import os
from openai import OpenAI

from edoc.gpt_helpers.connect import OpenAiConfig

OPENAI_API_KEY = OpenAiConfig.get_openai_api_key()

def create_chat_completion(messages, model='gpt-4o-mini'):
    """
    Create a chat completion using the OpenAI API.

    Args:
        messages (list): A list of message dictionaries for the conversation.
        model (str): The OpenAI model to use. Default is 'gpt-4o-mini'.

    Returns:
        str: The content of the response from the OpenAI API.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(messages=messages, model=model)
    return response.choices[0].message.content

def get_embedding(text, model="text-embedding-3-small"):
    """
    Generate an embedding for a given text using OpenAI's embedding model.

    Args:
        text (str): The text to be embedded. Newlines are replaced with spaces.
        model (str): The OpenAI model to use. Default is 'text-embedding-3-small'.

    Returns:
        list: A list of floats representing the embedding vector of the input text.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding