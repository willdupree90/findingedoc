from edoc.gpt_helpers.connect import connect_to_neo4j
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
    kg = connect_to_neo4j()
    magic_keyword = "Delete"
    if keyword == magic_keyword:  # Example dangerous keyword
        try:
            kg.query("MATCH (n) DETACH DELETE n")  
            return "Graph data deleted successfully!"
        except Exception as e:
            return f"An error occurred: {e}"
    else:
        return f"Incorrect keyword! Action not performed. To delete KG data enter '{magic_keyword}'"