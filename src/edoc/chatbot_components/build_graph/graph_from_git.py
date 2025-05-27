import os
import gradio as gr

from git import Repo, GitCommandError

from edoc.kg_construction.bulk_load import CodebaseGraph

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

def create_graph_from_git(git_url, model, git_token=None, use_branch=None, progress=gr.Progress(track_tqdm=True)):
    """
    Create a knowledge graph from a GitHub repository.

    This function clones a GitHub repository, processes the codebase, and generates 
    a knowledge graph. If the API key is not set, an error is returned.

    Args:
        git_url (str): The URL of the GitHub repository.
        git_token (str, optional): GitHub Personal Access Token for private repos.
        use_branch (str): The branch to clone (default is 'main').
        model (str): The LLM model to use. Defaults from env, see llm_client.py
        progress (gr.Progress, optional): Gradio's progress tracker.

    Returns:
        str: Success message or an error message.
    """
    root_dir = get_project_root_from_github(git_url, git_token, use_branch)
    if root_dir is not None:
        codebase_graph = CodebaseGraph(root_directory=root_dir, model=model)
        codebase_graph.create_graph()

        return "Successfully created graph from Git project."
    
    return "Could not successfully clone Git, did not extract to graph."