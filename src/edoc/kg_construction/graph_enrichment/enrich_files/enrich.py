from tqdm import tqdm
import json
from edoc.kg_construction.graph_enrichment.enrich_files.file_chunking import get_text_splitter, read_file_contents
from edoc.kg_construction.graph_enrichment.enrich_files.summarize_chunks import summarize_file_chunk
from edoc.kg_construction.graph_enrichment.enrich_files.entity_extraction import extract_code_entities
from edoc.gpt_helpers.gpt_basics import get_embedding

class FileEnrichmentHandler:
    def __init__(
            self, 
            kg,
            chunk_size=3500,
            chunk_overlap=50
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

    def enrich_file_nodes(self):
        """
        Enriches the knowledge graph by processing files, creating and linking code chunks, and extracting unique code entities.
        """

        # Query to find files without chunk nodes
        query = """
        MATCH (file:File)
        WHERE NOT (file)-[:CONTAINS]->()
        RETURN file.path AS file_path
        """

        result = self.kg.query(query)
        file_paths = [record['file_path'] for record in result]

        for file in tqdm(file_paths, desc='Creating chunks from files'):
            file_contents = read_file_contents(file)

            if file_contents is not None:
                text_splitter, splitter_language = get_text_splitter(file, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)

                chunks = text_splitter.split_text(file_contents)

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
                            chunk.chunk_embedding = $chunk_embedding,
                            chunk.chunk_splitter_used = $splitter_language
                        WITH chunk
                        MATCH (file:File {path: $file_path})
                        MERGE (file)-[:CONTAINS]->(chunk)
                    """, {
                        'chunk_id': chunk_id,
                        'raw_code': chunk,
                        'summary': chunk_summary,
                        'summary_embedding': summary_embedding,
                        'chunk_embedding': chunk_embedding,
                        'file_path': file,
                        'splitter_language': splitter_language
                    })

                    try:
                        chunk_entities = extract_code_entities(chunk)
                    except Exception as e:
                        print(f"An error occurred while extracting entities (import, func, class) in a chunk for Chunk [{chunk_id}]: {e} \n Passed extracting entities")
                        continue

                    for imp in chunk_entities['imports']:
                        module_name = imp['module']
                        if module_name not in unique_imports:
                            unique_imports[module_name] = set(imp['entities'])
                        else:
                            unique_imports[module_name].update(imp['entities'])

                    for func in chunk_entities['functions']:
                        func_name = func['name']
                        if func_name not in unique_functions:
                            unique_functions[func_name] = {
                                'parameters': json.dumps([{'name': param['name'], 'type': param['type']} for param in func['parameters']]),
                                'return_type': func['return_type']
                            }

                    for cls in chunk_entities['classes']:
                        cls_name = cls['name']
                        if cls_name not in unique_classes:
                            unique_classes[cls_name] = {
                                'parameters': json.dumps([{'name': param['name'], 'type': param['type']} for param in cls['parameters']])
                            }

                # Store unique entities in the graph

                for name, entities in unique_imports.items():
                    self.kg.query("""
                        MERGE (import:Import {name: $name, file_path: $file_path})
                        SET import.entities = $entities
                        WITH import
                        MATCH (file:File {path: $file_path})
                        MERGE (file)-[:CALLS]->(import)
                    """, {
                        'name': name,
                        'entities': list(entities),
                        'file_path': file
                    })

                for name, func in unique_functions.items():
                    self.kg.query("""
                        MERGE (function:Function {name: $name, file_path: $file_path})
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

                for name, cls in unique_classes.items():
                    self.kg.query("""
                        MERGE (class:Class {name: $name, file_path: $file_path})
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