from edoc.rag_components.responder import BuildResponse

def response(message, history, model):
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
    responder = BuildResponse(model=model)

    try:
        response = responder.get_full_response(
            question=message,
            top_k=2,
            next_chunk_limit=1
        )
        return response
    except Exception as e:
        return f"An error occurred while processing your request: {e}."