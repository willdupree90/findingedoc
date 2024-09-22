import gradio as gr
from edoc.gpt_helpers.connect import OpenAiConfig
from edoc.chatbot_components.utils import response, set_openai_api_key, create_graph_from_zip, create_graph_from_git, delete_graph_data

OPENAI_API_KEY = OpenAiConfig.get_openai_api_key()

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
            gr.Markdown("## Choose Your Method to Upload Code Files")

            upload_output = gr.Textbox(label="Graph Progress")

            with gr.Group():
                gr.Markdown("### Upload Your Zipped Code Files")
                upload_zip_button = gr.UploadButton(label="Select ZIP File", file_types=[".zip"], file_count="single")
                upload_zip_button.upload(create_graph_from_zip, upload_zip_button, upload_output)

            with gr.Group():
                gr.Markdown("### Import Your Git Project via URL")
                with gr.Row():
                    upload_git_input = gr.Textbox(label="Upload Your Git Project via URL")
                    set_access_token = gr.Textbox(label="Set Access Token (Optional)")
                    set_branch = gr.Textbox(label="Set Git Branch (if not 'main')")

                upload_git_button = gr.Button("Import Git Project")

                upload_git_button.click(create_graph_from_git, [upload_git_input, set_access_token, set_branch], upload_output) 

        with gr.Tab("Delete data"):
            keyword_input = gr.Textbox(label="Please enter 'Delete' to remove data.")
            submit_button = gr.Button("Submit")

            delete_output = gr.Textbox(label="Output")
            submit_button.click(delete_graph_data, inputs=keyword_input, outputs=delete_output)

if __name__ == "__main__":
    demo.launch(share=True)
