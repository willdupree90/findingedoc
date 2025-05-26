import gradio as gr
import os
import zipfile

from edoc.llm_helpers.connect import OpenAiConfig

from edoc.kg_construction.bulk_load import CodebaseGraph

def get_project_root_from_temp_location(zip_file):
    """
    Extract the contents of a ZIP file and return the path to the extracted directory.

    This function extracts a ZIP file into a designated local directory, ensuring the 
    structure is cross-platform compatible. It expects that the ZIP contains a single 
    root directory.

    Args:
        zip_file (file): The ZIP file to be extracted.

    Returns:
        str: The path to the extracted project directory or None if an error occurs.
    """
    # Create an upload directory inside your system
    upload_dir = os.path.normpath("../../edocSourceData")  # Local directory for testing

    os.makedirs(upload_dir, exist_ok=True)  # Ensure the directory exists

    try:
        with zipfile.ZipFile(zip_file.name, 'r') as zip_ref:
            zip_ref.extractall(upload_dir)
    except Exception as e:
        print(f"Error extracting zip file: {e}")

    # Use os.path to handle cross-platform path splitting
    root_name = os.path.basename(zip_file.name)  # Get the file name
    root_name = os.path.splitext(root_name)[0]   # Strip the '.zip' extension
    extracted_project_root = os.path.join(upload_dir, root_name)

    if not os.path.exists(extracted_project_root):
        return None
    
    return extracted_project_root
    
def create_graph_from_zip(zip_file, progress=gr.Progress(track_tqdm=True)):
    """
    Create a knowledge graph from a ZIP file.

    This function extracts the ZIP file, processes the codebase, and generates 
    a knowledge graph. If the API key is not set, an error is returned.

    Args:
        zip_file (file): The ZIP file containing the codebase.
        progress (gr.Progress, optional): Gradio's progress tracker.

    Returns:
        str: Success message or an error message.
    """
    #Check if the key is in env file
    #Force a component for setting key if not
    api_key_set = False
    OPENAI_API_KEY = OpenAiConfig.get_openai_api_key()
    if OPENAI_API_KEY is not None:
        api_key_set=True
    if not api_key_set:
        return "Error: Please provide an OpenAI API key in `Manage` dropdown before using the chatbot."

    root_dir = get_project_root_from_temp_location(zip_file)
    if root_dir is not None:
        codebase_graph = CodebaseGraph(root_directory=root_dir)
        codebase_graph.create_graph()

        return "Successfully created graph from directory."
    
    return "Could not successfully read file from zip. \nEnsure the ZIP file contains a single root directory (top-level folder) that shares the ZIP's name. All other files, folders, and subdirectories are then placed inside that root directory."

