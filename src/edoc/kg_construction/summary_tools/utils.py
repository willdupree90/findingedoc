import os
from edoc.gpt_helpers.gpt_basics import create_chat_completion

def generate_ascii_structure(root_directory, model='gpt-4o-mini'):
    """
    Generates an ASCII file structure from the root directory using OpenAI's language model.

    Args:
        root_directory (str): The root directory to summarize.
        model (str): The OpenAI model to use. Default is 'gpt-4o-mini'.

    Returns:
        str: The ASCII file structure summarized by the model.
    """
    root_directory = str(root_directory)

    file_structure = ""
    for root, dirs, files in os.walk(root_directory):
        # Calculate the level of depth (indentation)
        # to use replace root must be string
        root = str(root)
        level = root.replace(root_directory, '').count(os.sep)
        indent = ' ' * 4 * level
        # Add directory
        file_structure += f"{indent}{os.path.basename(root)}/\n"
        # Add files within the directory
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            file_structure += f"{sub_indent}{f}\n"

    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"I have the following file structure:\n{file_structure}\nPlease convert this into a clean and simple ASCII tree format. No need for any extra words, just the tree please."}
    ]
    
    ascii_tree = create_chat_completion(messages=prompt, model=model)
    
    return ascii_tree

def summarize_list_of_chunks(chunk_data, model='gpt-4o-mini'):
    """
    Summarize a list of summaries to make global understanding.

    Args:
        model (str): The OpenAI model to use. Default is 'gpt-4o-mini'.
        chunk_data (dict): A dictionary of name metadata and list  of chunk summaries

    Returns:
        str: A brief and clear summary of the chunk.
    """

    context = "Given context: "

    file_path = chunk_data['file_path']
    #Get nameless chunks have to add metadata
    chunk_context = '\n'.join([f'Chunk summareis for file {file_path}: '] + [f'Chunk {i} summary: '+summary for i, summary in enumerate(chunk_data['chunk_summaries'])])
    
    context += '\n' + chunk_context

    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"""We are trying to gain understanding around a coding project. A file may have chunks (snippets of the file).
         Can you aggregate and make summaries of a list of summaries from the given context? The goal is to build higher-level summaries of items downstream, 
         so please try and capture themes across items.

         Try to keep the summary, simple, concise, clear and structured using the following format:

         ### File Summary
        <Summarized details across chunks>
        
         Here is the list of chunk summaries:
         
         {context}"""}
    ]
    return create_chat_completion(messages=prompt, model=model)

def summarize_list_of_files_and_subdirs(model='gpt-4o-mini', file_data=None, subdir_data=None):
    """
    Summarize a list of summaries to make global understanding.

    Args:
        model (str): The OpenAI model to use. Default is 'gpt-4o-mini'.
        file_data (dict): A dictionary of name metadata and dict of [file summaries, file names]
        subdir_data (dict): A dictionary of name metadata and dict  of [subdirectory summaries, subdirectory names]

    Returns:
        str: A brief and clear summary of the chunk.
    """

    context = "Given context: "

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
        {"role": "user", "content": f"""We are trying to gain understanding around a coding project. A directory may have a mix of files or subdirectories.
         Can you aggregate and make summaries of a list of summaries from the given context? The goal is to build higher-level summaries of items downstream, 
         so it is important we only summarize information up to the current level (e.g., a directory summary only details contained files or subdirectories). 
         Please try and capture themes across items. If there is a lack of detail to summarize simply say so.

         Try to keep the summary simple, concise, clear and structured using the following format:

         ### Summary
         - **File Overview**: <Provide a general summary of files contained in the focused directory.>
         - **Subdirectory Overview**: <Summarize the contents of subdirectories contained within the directory.>
        
         Here is the list of summaries:
         
         {context}"""}
    ]
    return create_chat_completion(messages=prompt, model=model)