import openai
import gradio as gr
import os
import zipfile

from git import Repo, GitCommandError

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

def response(message, history):
    """
    Generate a chatbot response based on user input and chat history.

    This function uses a pre-built responder model to get a response based on the user's
    question, using a knowledge graph for context. It returns an error message if the 
    OpenAI API key has not been set.

    Args:
        message (str): The user's question.
        history (list): The chat history up to this point.

    Returns:
        str: The chatbot's response or an error message.
    """
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
    if not api_key_set:
        return "Error: Please provide an OpenAI API key in `Manage` dropdown before using the chatbot."

    root_dir = get_project_root_from_temp_location(zip_file)
    if root_dir is not None:
        codebase_graph = CodebaseGraph(root_directory=root_dir)
        codebase_graph.create_graph()

        return "Successfully created graph from directory."
    
    return "Could not successfully read file from zip. \nEnsure the ZIP file contains a single root directory (top-level folder) that shares the ZIP's name. All other files, folders, and subdirectories are then placed inside that root directory."

def get_project_root_from_github(repo_url, git_token=None, use_branch=None):
    """
    Clone a GitHub repository and return the path to the project root.
    
    Args:
        repo_url (str): The URL of the GitHub repository to clone.
        git_token (str, optional): GitHub Personal Access Token for private repos.
        use_branch (str): The branch to clone (default is 'main').
        
    Returns:
        str: Path to the root of the cloned project or none.
    """
    # Create an upload directory inside your system
    upload_dir = os.path.normpath("../../edocSourceData")  # Local directory for testing

    os.makedirs(upload_dir, exist_ok=True)  # Ensure the directory exists

    # If a token is provided, modify the repo URL to include the token for authentication
    if git_token:
        # Format the repo URL with the token
        repo_url = repo_url.replace("https://", f"https://{git_token}@")

    # Extract the repo name from the URL to use as the folder name
    repo_name = os.path.splitext(os.path.basename(repo_url))[0]
    project_dir = os.path.join(upload_dir, repo_name)

    branch = 'main'
    if use_branch:
        branch = use_branch

    try:
        # Clone the repo into the specified directory
        Repo.clone_from(repo_url, project_dir, branch=branch)
    except GitCommandError as e:
        if "Authentication failed" in str(e):
            print("Error: Authentication failed. Please check your GitHub token.")
        else:
            print(f"Error cloning GitHub repository: {e}")
            return None
    except Exception as e:
        print(f"Error cloning GitHub repository: {e}")
        return None

    # Return the project directory path
    if not os.path.exists(project_dir):
        return None
    
    return project_dir

def create_graph_from_git(git_url, git_token=None, use_branch=None, progress=gr.Progress(track_tqdm=True)):
    """
    Create a knowledge graph from a GitHub repository.

    This function clones a GitHub repository, processes the codebase, and generates 
    a knowledge graph. If the API key is not set, an error is returned.

    Args:
        git_url (str): The URL of the GitHub repository.
        git_token (str, optional): GitHub Personal Access Token for private repos.
        use_branch (str): The branch to clone (default is 'main').
        progress (gr.Progress, optional): Gradio's progress tracker.

    Returns:
        str: Success message or an error message.
    """
    if not api_key_set:
        return "Error: Please provide an OpenAI API key in `Manage` dropdown before using the chatbot."

    root_dir = get_project_root_from_github(git_url, git_token, use_branch)
    if root_dir is not None:
        codebase_graph = CodebaseGraph(root_directory=root_dir)
        codebase_graph.create_graph()

        return "Successfully created graph from Git project."
    
    return "Could not successfully clone Git, did not extract to graph."

# Function to delete graph data

def delete_graph_data(keyword):
    """
    Delete all nodes and relationships from the knowledge graph.

    This function clears the entire knowledge graph by running a `MATCH (n) DETACH DELETE n`
    Cypher query if the correct keyword is provided.

    Args:
        keyword (str): The keyword to trigger the deletion. Must be 'Delete'.

    Returns:
        str: Success message or an error message.
    """
    magic_keyword = "Delete"
    if keyword == magic_keyword:  # Example dangerous keyword
        try:
            kg.query("MATCH (n) DETACH DELETE n")  
            return "Graph data deleted successfully!"
        except Exception as e:
            return f"An error occurred: {e}"
    else:
        return f"Incorrect keyword! Action not performed. To delete KG data enter '{magic_keyword}'"