import os
from edoc.llm_helpers.llm_client import get_llm_client

def summarize_file_chunk(chunk_text, file_name, model=None):
    """
    Summarize a chunk of text from a file using OpenAI's language model.

    Args:
        chunk_text (str): The text chunk to summarize.
        file_name (str): The name of the file from which the chunk was extracted.
        model (str): The OpenAI model to use. Default is 'gpt-4o-mini'. See `llm_client.py`.

    Returns:
        str: A brief and clear summary of the chunk.
    """
    llm_client = get_llm_client(
        provider=os.getenv("OPENAI_PROVIDER", "openai"),
        model_name=model
    )

    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"""You are helping to summarize code chunks. 
        Please summarize the given chunk of text from the file `{file_name}`. 
        Keep the summary brief and clear, focusing on what the code does.

        The chunk codes is: {chunk_text}

        Please format summaries in markdown using this tempalte:
        **Summary**:
        <fill in>"""}
    ]
    
    return llm_client.chat_completion(messages=prompt)