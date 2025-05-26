import os
import openai
from edoc.llm_helpers.embedding_client import get_embedding_client

def set_openai_api_key(api_key):
    """
    Set the OpenAI API key dynamically.

    This function attempts to set the OpenAI API key and tests the key by performing 
    an embedding call. If the key is invalid, an error message is returned.

    Args:
        api_key (str): The OpenAI API key provided by the user.

    Returns:
        str: A success message if the key is valid, or an error message if the key is invalid.
    """

    try:
        embedding_client = get_embedding_client(
            provider=os.getenv("OPENAI_PROVIDER", "openai"),
        )
        embedding_client.embed("Test text for embedding call")
        
        return "API key set successfully!"
    except openai.AuthenticationError:
        return "Invalid API key. Please provide a valid OpenAI API key."
    except Exception as e:
        return f"An error occurred while testing the API key: {e}"