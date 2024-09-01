from edoc.gpt_helpers.gpt_basics import create_chat_completion

def summarize_list_of_summaries(summaries, model='gpt-4o-mini'):
    """
    Summarize a chunk of text from a file using OpenAI's language model.

    Args:
        summaries (lst[str]): The text chunk to summarize.
        model (str): The OpenAI model to use. Default is 'gpt-4o-mini'.

    Returns:
        str: A brief and clear summary of the chunk.
    """
    context = '\n'.join(summaries)

    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"I have these summaries {context}. \nPlease merge them into ovearching themes by summarizing them in simple terms. Try to keep the summary brief, but maintain clarity."}
    ]
    return create_chat_completion(messages=prompt, model=model)