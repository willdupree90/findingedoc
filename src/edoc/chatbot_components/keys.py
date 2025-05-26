import openai
from edoc.llm_helpers.connect import OpenAiConfig
from edoc.llm_helpers.gpt_basics import get_embedding

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
    global api_key_set
    try:
        # Set the new API key
        OpenAiConfig.set_openai_api_key(api_key)

        get_embedding("Test text for embedding call")
        
        api_key_set = True
        return "API key set successfully!"
    except openai.AuthenticationError:
        return "Invalid API key. Please provide a valid OpenAI API key."
    except Exception as e:
        return f"An error occurred while testing the API key: {e}"