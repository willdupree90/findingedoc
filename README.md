
# FindingEdoc
![Finding Edoc Banner](graph_banner.png)
In this project, we will use generative AI, knowledge graphs, and Retrieval-Augmented Generation (RAG) to help developers explore codebases via a chatbot.

## How to Use

### 1. Setting Up Your Environment

Before you can start filling your Neo4j database or using the chatbot, you'll need to set up your environment. This includes obtaining necessary API keys and configuring environment variables.

#### 1.1 Obtain an OpenAI API Key

1. Sign up for an OpenAI account if you don't have one.
2. Visit the OpenAI API page and create an API key.
3. Keep this key handy, as you'll need it in the next step.

#### 1.2 Create an `.env` File

The `.env` file will store your environment variables, including credentials for Neo4j and OpenAI, as well as an optional file location for seeding the database.

1. In the root directory of your project, create a file named `.env`.
2. Add the following environment variables to your `.env` file:

    ```plaintext
    NEO4J_USERNAME=your_neo4j_username
    NEO4J_PASSWORD=your_neo4j_password
    OPENAI_API_KEY=your_openai_api_key
    SEED_DATA=optional_path_to_your_seed_data_directory
    ```

- **`NEO4J_USERNAME`**: Your Neo4j database username (we suggest leaving as `neo4j`).
- **`NEO4J_PASSWORD`**: Your Neo4j database password.
- **`OPENAI_API_KEY`**: The API key you obtained from OpenAI.
- **`SEED_DATA`**: (Optional) Path to the directory where your data files are stored, which will be used to seed the Neo4j database.

#### 1.3 Set Up the Python Environment

Make sure you have Docker and Python set up as per the instructions provided earlier in the README. This will involve:

- Installing Docker and Python (if you haven't already).
- Setting up Docker and the Python virtual environment as described in the Environment Setup section.

### 2. Filling the Neo4j Database

Once your environment is set up, you'll need to fill your Neo4j database with data extracted from your codebase. This process involves running a bulk load script that processes your data and populates the database.

#### 2.1 Run the Bulk Load Script
Start python environment:
```bash
workon your_env
```

Navigate to the directory containing the bulk load script:

```bash
cd findingedoc/src/edoc/kg_construction/
```

Then, run the bulk load script from the command line:

```bash
python bulk_load.py
```

This script will:

1. **Connect to Neo4j**: Using the credentials provided in your `.env` file.
2. **Process Your Codebase**: Extract entities, summarize them, and store the information in Neo4j.
3. **Generate Embeddings**: Create vector embeddings for the nodes in the graph, preparing them for advanced search and analysis.

If you specified a path for `SEED_DATA` in your `.env` file, the script will automatically use that path. Otherwise, you should add a path like so:
```bash
python bulk_load.py \example\path\to_directory
```

### 3. Running the Chatbot

Once the database is populated, you can interact with the data through the chatbot interface.

#### Steps to run the chatbot:

1. Open a terminal or command prompt.
2. Navigate to the project directory: `findingedoc\src\edoc`.
3. Run the following command to start the chatbot:
   ```bash
   python chatbot.py
   ```

## Environment Setup

### Docker Setup

We will be using Docker to manage dependencies and run services like Neo4j, which is integral to the project.

#### Steps:

1. Install Docker if you haven't already.

2. Navigate to the root of the project.

3. Start the service by running `docker-compose up` from the command line. This will set up the environment, including Neo4j.

4. Once the service is up, access the Neo4j database at [http://localhost:7474](http://localhost:7474).

5. When finished, stop the service by running `docker-compose down`.

### Python Environment

Set up the python code necessary to run the project.

#### Steps:

1. Create a virtual environment using the terminal.
   - We use Python 3.11 for this project.
   - `mkvirtualenv -p python3.11 your_env`

2. Activate and work on your environment using:
   - `workon your_env`

3. To install the necessary packages, including development dependencies, navigate to `src` and run:
   - `pip install -e .`

## Relevant Links and Resources

- [Neo4j Docker Image Documentation](https://hub.docker.com/_/neo4j)
- [Python 3.11 Documentation](https://docs.python.org/3.11/)
