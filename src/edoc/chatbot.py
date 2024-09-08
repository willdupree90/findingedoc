import gradio as gr
from edoc.rag_components.responder import BuildResponse

responder = BuildResponse(model="gpt-4o-mini")

def response(message, history):
    return responder.get_response(question=message)

demo = gr.ChatInterface(response)

if __name__ == "__main__":
    demo.launch(share=True)