from edoc.rag_components.unstructured_retrievers import create_vector_index, perform_similarity_search, extract_code_entities
from langchain_community.graphs import Neo4jGraph

def _dir_file_structured_retriever(kg: Neo4jGraph, question: str, top_k: int) -> str:
    """
    Collects the neighborhood of entities mentioned in the question by:
    1. Performing a similarity search to find relevant chunks.
    2. Extracting named entities (functions, classes, imports) from the question.
    3. Querying the knowledge graph for the entities and related information, including directory and file summaries.
    
    Args:
        kg (Neo4jGraph): The kg object to connect too
        question (str): The user question for which to retrieve structured information.
        top_k (int): The number of top results to retrieve from the similarity search.
    
    Returns:
        str: A formatted string containing the results of the neighborhood search.
    """
    # Step 1: Perform similarity search over vector indexes for relevant chunks
    file_summary_index = create_vector_index("fileSummaryVectorIndex", "file_keyword", "File", "summary_embedding", ["name"])
    dir_summary_index = create_vector_index("dirSummaryVectorIndex", "dir_keyword", "Directory", "summary_embedding", ["name"])

    vector_indexes = [file_summary_index, dir_summary_index]
    
    similarity_results = perform_similarity_search(vector_indexes, question, top_k=top_k)
    files_from_similarity_search = [item.replace('\nname: ', '') for item in similarity_results]
    
    # Step 2: Extract entities (functions, classes, imports, directories, files) from the question
    entities = extract_code_entities(question)
    entities.extend(files_from_similarity_search)
    entities = list(set(entities))

    # Define an empty list to hold the final output
    final_summaries = []
    
    # List of attributes to search by
    search_attributes = ['name', 'path']

    for name_or_path in entities:
        
        # Query to handle files (finding the file and its parent directories)
        file_query_template = """
        OPTIONAL MATCH (file:File {{{attribute}: $name_or_path}})
        WITH file
        OPTIONAL MATCH (parent_dir:Directory)-[:CONTAINS*]->(file)
        RETURN file.path AS file_path, file.name AS file_name, file.summary AS file_summary,
               collect(parent_dir.name) AS parent_dirs
        """

        # Query to handle directories (find the directory and its parent directories)
        dir_query_template = """
        OPTIONAL MATCH (dir:Directory {{{attribute}: $name_or_path}})
        WITH dir
        OPTIONAL MATCH (parent_dir:Directory)-[:CONTAINS*]->(dir)
        RETURN dir.path AS dir_path, dir.name AS dir_name, dir.summary AS dir_summary,
               collect(parent_dir.name) AS parent_dirs
        """
        
        params = {"name_or_path": name_or_path}
        
        # Iterate over the search attributes (name, path) to dynamically search for files
        for attr in search_attributes:
            file_query = file_query_template.format(attribute=attr)
            file_result = kg.query(file_query, params)
            
            # If a file is found, process the result and store context
            if file_result:
                for record in file_result:
                    file_path = record.get("file_path")
                    file_name = record.get("file_name")
                    file_summary = record.get("file_summary", "No summary available")
                    parent_dirs = record.get("parent_dirs", [])
                    
                    if file_name is not None:
                        # Build the file's summary context
                        summary_context = (f"File: {file_name} ({file_path})\n"
                                        f"File Summary: {file_summary}\n"
                                        f"Parent Directories: {', '.join(parent_dirs)}")
                        final_summaries.append(summary_context)
        
        # Iterate over the search attributes (name, path) to dynamically search for directories
        for attr in search_attributes:
            dir_query = dir_query_template.format(attribute=attr)
            dir_result = kg.query(dir_query, params)
            
            # If a directory is found, process the result and store context
            if dir_result:
                for record in dir_result:
                    dir_path = record.get("dir_path")
                    dir_name = record.get("dir_name")
                    dir_summary = record.get("dir_summary", "No summary available")
                    parent_dirs = record.get("parent_dirs", [])
                    
                    if dir_name is not None:
                        # Build the directory's summary context
                        summary_context = (f"Directory: {dir_name} ({dir_path})\n"
                                        f"Directory Summary: {dir_summary}\n"
                                        f"Parent Directories: {', '.join(parent_dirs)}")
                        final_summaries.append(summary_context)
    
    sep = "\n"+75*"="+"\n"
    dir_file_context = sep.join(final_summaries)
    
    return dir_file_context

#Langchain used functions expect a single dict param, wrap the input to pass to our function
def dir_file_structured_retriever(_dict):
    if "top_k" not in _dict.keys():
        _dict["top_k"] = 1
    
    return _dir_file_structured_retriever(kg=_dict["kg"], question=_dict["question"], top_k=_dict["top_k"])

