def _create_vector_index(kg, label, property_name="summary_embeddings", index_name=None, dimensions=1536):
        """
        Create a vector index for the specified label if it does not already exist.

        Args:
            kg (Neo4jGraph): graph object to complete cypher queries
            label (str): The label of the nodes (e.g., 'File', 'Directory', 'Chunk').
            property_name (str): The property name on which the vector index is created. Default is 'summary_embeddings'.
            index_name (str): The name of the index. If None, it will default to 'labelVectorIndex'.
            dimensions (int): The dimensionality of the vectors. Default is 1536.
        """
        if not index_name:
            index_name = f"{label.lower()}VectorIndex"

        query = f"""
        CREATE VECTOR INDEX {index_name} IF NOT EXISTS
        FOR (n:{label})
        ON n.{property_name}
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: {dimensions},
                `vector.similarity_function`: 'cosine'
            }}
        }}
        """
        try:
            kg.query(query)
            print(f"Vector index {index_name} for label {label} created successfully.")
        except Exception as e:
            print(f"An error occurred while creating the vector index: {e}")

def create_all_vector_indexes(kg):
    """
    Create vector indexes for chunks, files, and directories. The indexes are separated for chunks and summaries.

    Args:
            kg (Neo4jGraph): graph object to complete cypher queries
    """
    # Create index for chunks
    _create_vector_index(kg=kg, label="Chunk", property_name="chunk_embedding", index_name="chunkRawVectorIndex")
    _create_vector_index(kg=kg, label="Chunk", property_name="summary_embedding", index_name="chunkSummaryVectorIndex")

    # Create index for files and directories
    _create_vector_index(kg=kg, label="File", property_name="summary_embedding", index_name="fileSummaryVectorIndex")
    _create_vector_index(kg=kg, label="Directory", property_name="summary_embedding", index_name="dirSummaryVectorIndex")