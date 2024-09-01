from tqdm import tqdm
import json
from langchain.text_splitter import PythonCodeTextSplitter
from edoc.kg_construction.build_tools.utils import should_skip_file, read_file_contents, summarize_file_chunk, extract_code_entities
from edoc.gpt_helpers.gpt_basics import get_embedding

class GraphBuilder:
    def __init__(
            self, 
            kg,
            chunk_size=500,
            chunk_overlap=25
    ):
        """
        Initialize the CodebaseGraph with a connection to Neo4j.

        Args:
            kg (Neo4jGraph): graph object to complete cypher queries
            chunk_size (int): size of chunk to use (by number of tokens)
            chunk_overlap (int): number of chunks to overlap when splitting
        """
        self.kg = kg
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def enrich_graph(self):
        """
        Enriches the knowledge graph by processing files, creating and linking code chunks, and extracting unique code entities.
        """
        text_splitter = PythonCodeTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)

        # Query to find files without chunk nodes
        query = """
        MATCH (file:File)
        WHERE NOT (file)-[:CONTAINS]->(:Chunk)
        RETURN file.path AS file_path
        """

        result = self.kg.query(query)
        file_paths = [record['file_path'] for record in result]

        file_paths = [file for file in file_paths if not should_skip_file(file)]

        for file in tqdm(file_paths, desc='Creating chunks from files'):
            file_contents = read_file_contents(file)

            if file_contents is not None:
                chunks = text_splitter.split_text(file_contents)

                # Initialize collections for unique entities
                unique_imports = {}
                unique_functions = {}
                unique_classes = {}

                for idx, chunk in enumerate(chunks):
                    chunk_id = f"{file}_chunk_{idx:06d}"
                    chunk_summary = summarize_file_chunk(chunk_text=chunk, file_name=file)
                    summary_embedding = get_embedding(chunk_summary)
                    chunk_embedding = get_embedding(chunk)

                    # Create the chunk node and link it to the file
                    self.kg.query("""
                        MERGE (chunk:Chunk {id: $chunk_id})
                        SET chunk.raw_code = $raw_code, 
                            chunk.summary = $summary, 
                            chunk.summary_embedding = $summary_embedding, 
                            chunk.chunk_embedding = $chunk_embedding
                        WITH chunk
                        MATCH (file:File {path: $file_path})
                        MERGE (file)-[:CONTAINS]->(chunk)
                    """, {
                        'chunk_id': chunk_id,
                        'raw_code': chunk,
                        'summary': chunk_summary,
                        'summary_embedding': summary_embedding,
                        'chunk_embedding': chunk_embedding,
                        'file_path': file
                    })

                    # Extract and process code entities for each chunk
                    chunk_entities = extract_code_entities(chunk)

                    # Collect unique imports
                    for imp in chunk_entities['imports']:
                        module_name = imp['module']
                        if module_name not in unique_imports:
                            unique_imports[module_name] = set(imp['entities'])
                        else:
                            unique_imports[module_name].update(imp['entities'])

                    # Collect unique functions
                    for func in chunk_entities['functions']:
                        func_name = func['name']
                        if func_name not in unique_functions:
                            unique_functions[func_name] = {
                                'parameters': json.dumps([{'name': param['name'], 'type': param['type']} for param in func['parameters']]),
                                'return_type': func['return_type']
                            }

                    # Collect unique classes
                    for cls in chunk_entities['classes']:
                        cls_name = cls['name']
                        if cls_name not in unique_classes:
                            unique_classes[cls_name] = {
                                'parameters': json.dumps([{'name': param['name'], 'type': param['type']} for param in cls['parameters']])
                            }

                # Store unique entities in the graph

                # Create and link unique import nodes
                for module, entities in unique_imports.items():
                    self.kg.query("""
                        MERGE (import:Import {module: $module})
                        SET import.entities = $entities
                        WITH import
                        MATCH (file:File {path: $file_path})
                        MERGE (file)-[:CALLS]->(import)
                    """, {
                        'module': module,
                        'entities': list(entities),
                        'file_path': file
                    })

                # Create and link unique function nodes
                for name, func in unique_functions.items():
                    self.kg.query("""
                        MERGE (function:Function {name: $name})
                        SET function.parameters = $parameters, function.return_type = $return_type
                        WITH function
                        MATCH (file:File {path: $file_path})
                        MERGE (file)-[:DEFINES]->(function)
                    """, {
                        'name': name,
                        'parameters': func['parameters'],
                        'return_type': func['return_type'],
                        'file_path': file
                    })

                # Create and link unique class nodes
                for name, cls in unique_classes.items():
                    self.kg.query("""
                        MERGE (class:Class {name: $name})
                        SET class.parameters = $parameters
                        WITH class
                        MATCH (file:File {path: $file_path})
                        MERGE (file)-[:DEFINES]->(class)
                    """, {
                        'name': name,
                        'parameters': cls['parameters'],
                        'file_path': file
                    })

                # Link all chunks in sequence using APOC's `NEXT` relationship
                self.kg.query("""
                    MATCH (file:File {path: $file_path})-[:CONTAINS]->(chunk:Chunk)
                    WITH chunk ORDER BY chunk.id ASC
                    WITH collect(chunk) AS chunks
                    CALL apoc.nodes.link(chunks, 'NEXT')
                    RETURN count(*)
                """, {
                    'file_path': file
                })

    def _create_vector_index(self, label, property_name="summary_embeddings", index_name=None, dimensions=1536):
        """
        Create a vector index for the specified label if it does not already exist.

        Args:
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
            self.kg.query(query)
            print(f"Vector index {index_name} for label {label} created successfully.")
        except Exception as e:
            print(f"An error occurred while creating the vector index: {e}")

    def create_all_vector_indexes(self):
        """
        Create vector indexes for chunks, files, and directories. The indexes are separated for chunks and summaries.
        """
        # Create index for chunks
        self._create_vector_index(label="Chunk", property_name="chunk_embeddings", index_name="chunkRawVectorIndex")
        self._create_vector_index(label="Chunk", property_name="summary_embeddings", index_name="chunkSummaryVectorIndex")

        # Create index for files and directories
        self._create_vector_index(label="File", property_name="summary_embeddings", index_name="fileSummaryVectorIndex")
        self._create_vector_index(label="Directory", property_name="summary_embeddings", index_name="dirSummaryVectorIndex")