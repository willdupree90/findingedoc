
# Neo4j Graph Query: Breadth and Depth Exploration

This document provides examples of Cypher queries for exploring a Neo4j graph that represents the structure of a software project. The graph contains the following nodes:

## Nodes

- **Directory**: Represents a folder in a project.
- **File**: Represents a file in a project folder. The file may contain code or other data.
- **Chunk**: Represents a segment of code or content from a file.
- **Function**: Represents a function defined within a file.
- **Class**: Represents a class defined within a file.
- **Import**: Represents a library or module that has been imported into a file.

## Node Properties

- **Directory**: `{summary: STRING, summary_embedding: LIST, last_modified: STRING, created: STRING, path: STRING, name: STRING}`
- **File**: `{size: INTEGER, summary: STRING, summary_embedding: LIST, last_modified: STRING, created: STRING, path: STRING, name: STRING, type: STRING}`
- **Chunk**: `{chunk_embedding: LIST, chunk_splitter_used: STRING, id: STRING, raw_code: STRING, summary: STRING, summary_embedding: LIST}`
- **Import**: `{file_path: STRING, module: STRING, entities: LIST}`
- **Function**: `{name: STRING, file_path: STRING, parameters: STRING, return_type: STRING}`
- **Class**: `{file_path: STRING, parameters: STRING, name: STRING}`

## Relationships

- **(:Directory)-[:CONTAINS]->(:File)**
- **(:Directory)-[:CONTAINS]->(:Directory)**
- **(:File)-[:CALLS]->(:Import)**
- **(:File)-[:CONTAINS]->(:Chunk)**
- **(:File)-[:DEFINES]->(:Function)**
- **(:File)-[:DEFINES]->(:Class)**
- **(:Chunk)-[:NEXT]->(:Chunk)**

---

To execute queries in the Neo4j console replace placeholder param with real param (e.g., `$directory_name` to `"src"`)

## Breadth Queries

### 1. Retrieve All Files in a Directory and Subdirectories

This query retrieves all the files that are contained directly or indirectly within a directory.

```cypher
MATCH (dir:Directory {name: $directory_name})-[:CONTAINS*]->(file:File)
RETURN file.path AS file_path, file.name AS file_name, file.summary as file_summary
```

### 2. Retrieve All Functions and Classes in a File

This query retrieves all the functions and classes defined in a file.

```cypher
MATCH (file:File {path: $file_path})-[:DEFINES]->(entity)
WHERE entity:Function OR entity:Class
RETURN entity.name AS entity_name, labels(entity) AS entity_type
```

---

## Depth Queries

### 1. Retrieve the Previous, Current, and Next Chunks

This query retrieves the previous, current, and next chunks in a file.

```cypher
MATCH (chunk:Chunk {id: $chunk_id})
OPTIONAL MATCH (prev_chunk:Chunk)-[:NEXT]->(chunk)
OPTIONAL MATCH (chunk)-[:NEXT]->(next_chunk:Chunk)
RETURN prev_chunk.summary AS prev_summary, chunk.summary AS curr_summary, next_chunk.summary AS next_summary
```

### 2. Retrieve File Summary for a Specific Class or Function

This query retrieves the file and its summary for a given class or function.

```cypher
MATCH (entity)
WHERE (entity:Class OR entity:Function) AND entity.name = $name
MATCH (file:File)-[:DEFINES]->(entity)
RETURN file.path AS file_path, file.summary AS file_summary
```

### 3. Retrieve Full Context of an Import

This query retrieves the file and import details, including related entities in the file.

```cypher
MATCH (file:File)-[:CALLS]->(import:Import {module: $module})
OPTIONAL MATCH (file)-[:DEFINES]->(entity)
RETURN file.path AS file_path, import.entities AS import_entities, entity.name AS defined_entities
```

---

## Combining Breadth and Depth Queries

You can combine breadth and depth queries to answer complex questions, such as retrieving the entire context of a project. For example:

### Retrieve All Files and Their Summaries in a Directory and Functions Defined in Each

```cypher
MATCH (dir:Directory {path: $directory_path})-[:CONTAINS*]->(file:File)
OPTIONAL MATCH (file)-[:DEFINES]->(function:Function)
RETURN file.path AS file_path, file.summary AS file_summary, function.name AS function_name
```

This will retrieve all the files in a directory, their summaries, and any functions defined within those files.
