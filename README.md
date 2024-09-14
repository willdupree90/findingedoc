
# FindingEdoc
![Finding Edoc Banner](graph_banner.png)
In this project, we will use generative AI, knowledge graphs, and Retrieval-Augmented Generation (RAG) to help developers explore codebases via a chatbot.

## Table of Contents

## How to Use

### 1. Setting Up Your Environment

Before you can start  using the chatbot tool, you'll need to set up your environment. This includes obtaining necessary API keys and configuring environment variables.

Make sure you have Docker and Python set up as per the instructions provided later in the README. This will involve:

- Installing Docker and Python (if you haven't already).
- Setting up Docker and the Python virtual environment as described in the Environment Setup section.

### 2. Using Edoc for Code Question-Answer

Once your environment is set up, you can start using Edoc to perform code-related questions and answers through the chatbot interface.

#### 2.1 Start the Docker Service

To begin, make sure that the Docker service is running. This will start the Neo4j database required for the knowledge graph.

1. Open a terminal and navigate to the root directory of your project.
2. Start the Docker service with:
   ```bash
   docker-compose up
   ```

This will start the necessary services for Neo4j and any other components required by the project.

#### 2.2 Run the Gradio Chatbot Interface

Once the Docker service is up and running, launch the chatbot interface using Gradio. This will allow you to interact with the knowledge graph and ask questions about the codebase.

1. Open a terminal and activate your Python environment:
   ```bash
   workon your_env
   ```

2. Navigate to the directory containing the chatbot script:
   ```bash
   cd findingedoc/src/edoc
   ```

3. Run the chatbot interface using the following command:
   ```bash
   python chatbot.py
   ```

4. Once the Gradio interface starts, a link to access the chatbot interface will be displayed in your terminal. Open this link in your browser to interact with the chatbot.

#### 2.3 Using the Gradio Interface

The Gradio interface will provide several functionalities that allow you to upload graph data, set an API key, ask questions, and delete data from the knowledge graph.

- **Set OpenAI API Key**: 
  If you haven’t already set the `OPENAI_API_KEY` in the `.env` file, the Gradio interface will prompt you to input your OpenAI API key before interacting with the chatbot. The key will only be stored during the session.
  
- **Upload Graph Data**: 
  Use the "Upload files" tab to input the path to a directory containing your codebase. The files will be processed, and the knowledge graph will be populated with the extracted information.

- **Ask Questions**: 
  Once the graph is populated with data, you can ask the chatbot questions about the codebase, such as file structure, function definitions, classes, and other key entities.

- **Delete Graph Data**: 
  If you need to delete the current knowledge graph data, navigate to the "Delete data" tab, enter the keyword `Delete`, and submit. This will clear all the nodes and relationships in the Neo4j database.


## Environment Setup

### Environment Variables

#### 1. Obtain an OpenAI API Key

1. Sign up for an OpenAI account if you don't have one.
2. Visit the OpenAI API page and create an API key.
3. Keep this key handy, as you'll need it in the next step.

#### 2. Create an `.env` File

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
- **`OPENAI_API_KEY`**: (Optional) The API key you obtained from OpenAI. If you don't include it here, you will be prompted to provide it when you launch the chatbot.
- **`SEED_DATA`**: (Optional) Path to the directory where your data files are stored, which will be used to seed the Neo4j database.

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
