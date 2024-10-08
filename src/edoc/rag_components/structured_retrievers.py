from edoc.rag_components.unstructured_retrievers import create_vector_index, perform_similarity_search, extract_code_entities
from langchain_community.graphs import Neo4jGraph

def _dir_file_structured_retriever(kg: Neo4jGraph, question: str, top_k: int) -> str:
    """
    Collects the neighborhood of entities mentioned in the question by:
    1. Performing a similarity search to find relevant files and directories.
    2. Extracting named entities (files, directories, functions, classes, imports) from the question.
    3. Querying the knowledge graph for the entities and related information, including directory and file summaries.
    
    Args:
        kg (Neo4jGraph): The kg object to connect too
        question (str): The user question for which to retrieve structured information.
        top_k (int): The number of top results to retrieve from the similarity search.
    
    Returns:
        str: A formatted string containing the results of the neighborhood search.
    """
    file_summary_index = create_vector_index(
        vector_index_name="fileSummaryVectorIndex", 
        node_label="File", 
        embedding_property="summary_embedding", 
        text_properties=["name"]
    )

    dir_summary_index = create_vector_index(
        vector_index_name="dirSummaryVectorIndex",  
        node_label="Directory", 
        embedding_property="summary_embedding", 
        text_properties=["name"]
    )

    vector_indexes = [file_summary_index, dir_summary_index]
    
    similarity_results = perform_similarity_search(vector_indexes, question, top_k=top_k)
    files_from_similarity_search = [item.replace('\nname: ', '') for item in similarity_results]
    
    entities = extract_code_entities(question)
    entities.extend(files_from_similarity_search)
    entities = list(set(entities))

    final_summaries = []
    
    search_attributes = ['name', 'path']

    for name_or_path in entities:
        
        file_query_template = """
        OPTIONAL MATCH (file:File {{{attribute}: $name_or_path}})
        WITH file
        OPTIONAL MATCH (parent_dir:Directory)-[:CONTAINS*]->(file)
        RETURN file.path AS file_path, file.name AS file_name, file.summary AS file_summary,
               collect(parent_dir.name) AS parent_dirs
        """

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
                        summary_context = (f"Directory: {dir_name} ({dir_path})\n"
                                        f"Directory Summary: {dir_summary}\n"
                                        f"Parent Directories: {', '.join(parent_dirs)}")
                        final_summaries.append(summary_context)
    
    sep = "\n"+75*"="+"\n"
    dir_file_context = sep.join(final_summaries)
    
    return dir_file_context

#Langchain used functions expect a single dict param, wrap the input to pass to our function
def dir_file_structured_retriever(_dict):
    """
        Get the file and dir summary context

        Args:
            _dict (dict): keys include
                kg (Neo4jGraph): The kg object to connect too.
                question (str): The user's question.
                top_k (int): The number of top results to consider. Default is 1.

        Returns:
            str: The generated context.
        """
    if "top_k" not in _dict.keys():
        _dict["top_k"] = 1
    
    return _dir_file_structured_retriever(kg=_dict["kg"], question=_dict["question"], top_k=_dict["top_k"])

def _get_code_entity_node_attributes(node, node_type):
    """
    Extract specific attributes from a node depending on its type.
    """
    node_data = {"name": node.get("name", "")}  # Every node should have a 'name'

    if "Function" in node_type:
        node_data["node_type"] = "Function"
        node_data["parameters"] = node.get("parameters", "None")
        node_data["return_type"] = node.get("return_type", "None")
    elif "Class" in node_type:
        node_data["node_type"] = "Class"
        node_data["parameters"] = node.get("parameters", "None")
    elif "Import" in node_type:
        node_data["node_type"] = "Import"
        node_data["entities"] = node.get("entities", "None")
    
    return node_data

def _build_entity_context(result):
    """
    Build a context string for a given node, its parent file, and related nodes.
    """
    entity_context = ""

    for record in result:
        node = record.get("n")
        file = record.get("file")
        node_type =record.get("label")
        
        if node:
            node_data = _get_code_entity_node_attributes(node, node_type)
            file_name = file.get("name", "Unknown") if file else "Unknown"
            
            entity_context += (
                f"File: {file_name}\n"
                f"Entity Details: {node_data}\n"
                f"--------------------------------------------\n"
            )
    
    return entity_context

def _code_structured_retriever(kg: Neo4jGraph, question: str, top_k: int, next_chunk_limit: int) -> str:
    """
    Collects the neighborhood of entities mentioned in the question by:
    1. Performing a similarity search to find relevant chunks.
    2. Extracting named entities (functions, classes, imports) from the question.
    3. Querying the knowledge graph for the entities and related information, including directory and file summaries.
    
    Args:
        kg (Neo4jGraph): The kg object to connect too
        question (str): The user question for which to retrieve structured information.
        top_k (int): The number of top results to retrieve from the similarity search.
        next_chunk_limit (int): The number of chunks to the left/right to search in the NEXT chain
    
    Returns:
        str: A formatted string containing the results of the neighborhood search.
    """

    chunk_summary_index = create_vector_index(
        vector_index_name="chunkSummaryVectorIndex", 
        node_label="Chunk", 
        embedding_property="summary_embedding", 
        text_properties=["id"]
    )

    chunk_raw_index = create_vector_index(
        vector_index_name="chunkRawVectorIndex", 
        node_label="Chunk", 
        embedding_property="chunk_embedding", 
        text_properties=["id"]
    )

    vector_indexes = [chunk_summary_index, chunk_raw_index]
    
    similarity_results = perform_similarity_search(vector_indexes, question, top_k=top_k)
    chunks_from_similarity_search = [item.replace('\nid: ', '') for item in similarity_results]
    
    entities = extract_code_entities(question)
    entities = list(set(entities))

    final_summaries = []
    
    # 3. Look up chunk neighborhoods (N chunks before and after)
    for chunk_id in chunks_from_similarity_search:
        query = f"""
        MATCH (c:Chunk {{id: $chunk_id}})
        OPTIONAL MATCH (prev_chunks)-[:NEXT*..{next_chunk_limit}]->(c)
        OPTIONAL MATCH (c)-[:NEXT*..{next_chunk_limit}]->(next_chunks)
        WITH collect(prev_chunks.id) + collect(c.id) + collect(next_chunks.id) AS all_chunk_ids
        UNWIND all_chunk_ids AS unique_chunk_id
        MATCH (chunk:Chunk {{id: unique_chunk_id}})
        RETURN DISTINCT chunk.id, chunk.raw_code
        ORDER BY chunk.id ASC
        """
        result = kg.query(query, {"chunk_id": chunk_id})  # You can adjust N to include more/less chunks

        # Combine chunk neighborhood into the context
        chunk_context = ""
        for record in result:
            chunk_id = record.get("chunk.id")
            raw_code = record.get("chunk.raw_code", "")
            chunk_context += f"Chunk ID: {chunk_id}\nCode:\n{raw_code}\n\n"

        final_summaries.append(chunk_context)

    # 4. Look up imports, functions, and classes, capturing relationships
    for entity in entities:
        query = """
        OPTIONAL MATCH (n)
        WHERE (n:Import OR n:Function OR n:Class) AND n.name = $entity
        OPTIONAL MATCH (file:File)-[r]->(n)
        RETURN n, file, labels(n) AS label
        """
        result = kg.query(query, {"entity": entity})

        # Build the context for this entity
        entity_context = _build_entity_context(result)
        
        final_summaries.append(entity_context)
    
    sep = "\n"+75*"="+"\n"
    code_context = sep.join(final_summaries)
    
    return code_context

#Langchain used functions expect a single dict param, wrap the input to pass to our function
def code_structured_retriever(_dict):
    """
        Get code context by looking up chunks

        Args:
            _dict (dict): keys include
                kg (Neo4jGraph): The kg object to connect too.
                question (str): The user's question.
                top_k (int): The number of top results to consider. Default is 1.
                next_chunk_limit (int): The number of chunks to the left/right to search in the NEXT chain.

        Returns:
            str: The generated context.
        """
    
    if "top_k" not in _dict.keys():
        _dict["top_k"] = 1
    
    if "next_chunk_limit" not in _dict.keys():
        _dict["next_chunk_limit"] = 1
    
    return _code_structured_retriever(kg=_dict["kg"], question=_dict["question"], top_k=_dict["top_k"], next_chunk_limit=_dict["next_chunk_limit"])