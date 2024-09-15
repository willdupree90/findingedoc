import gradio as gr
from edoc.gpt_helpers.connect import OpenAiConfig
from edoc.chatbot_components.utils import response, set_openai_api_key, capture_directory_path, delete_graph_data

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
            # dir_input = gr.Textbox(label="Enter Directory Path (Warning: Submitting will process files through LLM and can take time).", placeholder="Enter or paste the path to your directory here...")
            # submit_button = gr.Button("Submit")
            upload_button = gr.UploadButton(label="Upload Your Zipped Code Files", file_types=[".zip"], file_count="single")
            output = gr.Textbox(label="Graph Progress")
            upload_button.upload(capture_directory_path, upload_button, output)
            

            # submit_button.click(capture_directory_path, inputs=dir_input, outputs=output)

        with gr.Tab("Delete data"):
            keyword_input = gr.Textbox(label="Please enter 'Delete' to remove data.")
            submit_button = gr.Button("Submit")

            output = gr.Textbox(label="Output")
            submit_button.click(delete_graph_data, inputs=keyword_input, outputs=output)

if __name__ == "__main__":
    demo.launch(share=True)
