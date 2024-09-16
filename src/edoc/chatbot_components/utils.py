import openai
import gradio as gr
import os
import zipfile

from edoc.gpt_helpers.gpt_basics import get_embedding
from edoc.rag_components.responder import BuildResponse
from edoc.kg_construction.bulk_load import CodebaseGraph
from edoc.gpt_helpers.connect import OpenAiConfig
from edoc.gpt_helpers.connect import connect_to_neo4j

#Check if the key is in env file
#Force a component for setting key if not
api_key_set = False
OPENAI_API_KEY = OpenAiConfig.get_openai_api_key()
if OPENAI_API_KEY is not None:
    api_key_set=True


kg = connect_to_neo4j()

def set_openai_api_key(api_key):
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

def response(message, history):
    if not api_key_set:
        return "Error: Please provide an OpenAI API key in `Manage` dropdown before using the chatbot."

    responder = BuildResponse(model="gpt-4o-mini")

    try:
        response = responder.get_full_response(
            question=message,
            top_k=2,
            next_chunk_limit=1
        )
        return response
    except Exception as e:
        return f"An error occurred while processing your request: {e}."

def get_project_root_from_temp_location(zip_file):
    # Create an upload directory inside your system
    upload_dir = os.path.normpath("../../edocSourceData")  # Local directory for testing

    os.makedirs(upload_dir, exist_ok=True)  # Ensure the directory exists

    try:
        with zipfile.ZipFile(zip_file.name, 'r') as zip_ref:
            zip_ref.extractall(upload_dir)
    except Exception as e:
        return f"Error extracting zip file: {e}"

    # Use os.path to handle cross-platform path splitting
    root_name = os.path.basename(zip_file.name)  # Get the file name
    root_name = os.path.splitext(root_name)[0]   # Strip the '.zip' extension
    extracted_project_root = os.path.join(upload_dir, root_name)

    if not os.path.exists(extracted_project_root):
        return None
    
    return extracted_project_root
    
    
def capture_directory_path(zip_file, progress=gr.Progress(track_tqdm=True)):

    if not api_key_set:
        return "Error: Please provide an OpenAI API key in `Manage` dropdown before using the chatbot."

    root_dir = get_project_root_from_temp_location(zip_file)
    if root_dir is not None:
        codebase_graph = CodebaseGraph(root_directory=root_dir)
        codebase_graph.create_graph()

        return "Successfully created graph from directory."
    
    return "Could not successfully read file from zip. \nEnsure the ZIP file contains a single root directory (top-level folder) that shares the ZIP's name. All other files, folders, and subdirectories are then placed inside that root directory."

# Function to delete graph data
def delete_graph_data(keyword):
    magic_keyword = "Delete"
    if keyword == magic_keyword:  # Example dangerous keyword
        try:
            kg.query("MATCH (n) DETACH DELETE n")  
            return "Graph data deleted successfully!"
        except Exception as e:
            return f"An error occurred: {e}"
    else:
        return f"Incorrect keyword! Action not performed. To delete KG data enter '{magic_keyword}'"