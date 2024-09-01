from edoc.gpt_helpers.gpt_basics import create_chat_completion

def summarize_list_of_summaries(model='gpt-4o-mini', chunk_data=None, file_data=None, subdir_data=None):
    """
    Summarize a list of summaries to make global understanding.

    Args:
        model (str): The OpenAI model to use. Default is 'gpt-4o-mini'.
        chunk_data (dict): A dictionary of name metadata and list  of chunk summaries
        file_data (dict): A dictionary of name metadata and dict of [file summaries, file names]
        subdir_data (dict): A dictionary of name metadata and dict  of [subdirectory summaries, subdirectory names]

    Returns:
        str: A brief and clear summary of the chunk.
    """

    context = "Given context: "

    chunk_context = 'No chunk context available.'
    if chunk_data is not None:
        file_path = chunk_data['file_path']
        #Get nameless chunks have to add metadata
        chunk_context = '\n'.join([f'Chunk summareis for file {file_path}: '] + [f'Chunk {i} summary: '+summary for i, summary in enumerate(chunk_data['chunk_summaries'])])
    
    context += '\n' + chunk_context

    file_context = 'No file context available.'
    if file_data is not None:
        dir_path = file_data['dir_path']
        #Get dict need to create context for list of file data
        file_context = '\n'.join([f'File summaries for {dir_path}: '] + [f"File '{name}': {summary}" for name, summary in zip(file_data['file_names'], file_data['file_summaries'])])
    
    context += '\n' + file_context

    subdir_context = 'No subdir context available. \n'
    if subdir_data is not None:
        dir_path = subdir_data['dir_path']
        subdir_context = '\n'.join([f'Subdirectory summaries for {dir_path}: '] + [f"Subdirectory '{name}': {summary}" for name, summary in zip(subdir_data['subdir_names'], subdir_data['subdir_summaries'])])

    context += '\n' + subdir_context

    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"""We are trying to gain understanding around a file system. It has directories, files, and chunks (snippets of the file).
         Can you aggregate and make summaries of a list of summaries from a mix of these items? The goal is to build higher level summaries of items downstream.
         Try to keep the summary brief, but maintain clarity.
         \nPlease merge the text I give into ovearching themes by summarizing them in simple terms. No need to confirm or editorialize. If there is
         limited context please do what you can, keeping the limited details given.
         
         The list of summaries is {context}. """}
    ]
    return create_chat_completion(messages=prompt, model=model)