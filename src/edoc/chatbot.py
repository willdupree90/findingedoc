import gradio as gr
from edoc.rag_components.responder import BuildResponse

responder = BuildResponse(model="gpt-4o-mini")

def response(message, history):

    response = responder.get_full_response(
        question=message,
        top_k=2,
        next_chunk_limit=1
    )
    return response

demo = gr.ChatInterface(response)

if __name__ == "__main__":
    demo.launch(share=True)