import gradio as gr
import openai
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

def capture_directory_path(path, progress=gr.Progress(track_tqdm=True)):
    progress(0, desc="Starting graph creation process...")

    codebase_graph = CodebaseGraph(root_directory=path)
    codebase_graph.create_graph()

    return "Successfully created graph from directory."

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

with gr.Blocks(fill_height=True) as demo:
    system_prompt = gr.Markdown(
        """
        ## Finding Edoc
        Ask me questions about the code in my knowledge graph!
        """
    )

    gr.ChatInterface(response)

    with gr.Accordion("Manage", open=False):

        if OPENAI_API_KEY is None:
            with gr.Tab("Set API Key"):
                api_key_input = gr.Textbox(label="Enter your OpenAI API key (Not stored after session)", placeholder="Enter your OpenAI API key here...")
                set_api_key_button = gr.Button("Set")
                api_key_output = gr.Textbox(label="Status")

                set_api_key_button.click(set_openai_api_key, inputs=api_key_input, outputs=api_key_output)

        with gr.Tab("Upload files"):
            dir_input = gr.Textbox(label="Enter Directory Path (Warning: Submitting will process files through LLM and can take time).", placeholder="Enter or paste the path to your directory here...")
            submit_button = gr.Button("Submit")
            output = gr.Textbox(label="Graph Progress")

            submit_button.click(capture_directory_path, inputs=dir_input, outputs=output)

        with gr.Tab("Delete data"):
            keyword_input = gr.Textbox(label="Please enter 'Delete' to remove data.")
            submit_button = gr.Button("Submit")

            output = gr.Textbox(label="Output")
            submit_button.click(delete_graph_data, inputs=keyword_input, outputs=output)

if __name__ == "__main__":
    demo.launch(share=True)
