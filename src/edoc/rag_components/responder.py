from edoc.gpt_helpers.connect import connect_to_neo4j
from edoc.rag_components.structured_retrievers import dir_file_structured_retriever, code_structured_retriever

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser

class BuildResponse:
    def __init__(self, model='gpt-4o-mini'):
        """
        Initialize CodebaseQA class with an LLM model and a Neo4j connection.

        Args:
            llm_model (str): The language model to use. Default is 'gpt-4o-mini'.

        """
        self.llm = ChatOpenAI(
            temperature=0,
            model=model
        )

        # Connect to Neo4j database
        self.kg = connect_to_neo4j()

        # Initialize chain
        self.chain = None

        self.retriever_map = {
            "summary_question" : dir_file_structured_retriever,
            "code_question" : code_structured_retriever
        }


    def setup_chain(self, structured_retriever):
        """
        Set up the prompt, template, and processing chain for answering questions.

        Args:
            structured_retriever (callable): A structured retriever to fetch context from the knowledge graph.
        """

        template = """Answer the question using the following context, if you are unsure say so:
        {context}

        Question: {question}

        Use natural language and be concise.

        Answer:"""


        prompt = ChatPromptTemplate.from_template(template)

        chain = (
            RunnableParallel(
                {
                    "context": RunnablePassthrough() | structured_retriever,
                    "question": RunnablePassthrough(),
                }
            )
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return chain

    def get_response(self, question, top_k: int = 1, next_chunk_limit: int = 1, structured_retriever_key="summary_question"):
        """
        Get the response by invoking the chain with the question and relevant context.

        Args:
            question (str): The user's question.
            top_k (int): The number of top results to consider. Default is 1.
            structured_retriever_key (str): key that names which retriever to use.
            next_chunk_limit (int): The number of chunks to the left/right to search in the NEXT chain

        Returns:
            str: The generated answer from the LLM.
        """

        retriever = self.retriever_map.get(structured_retriever_key, dir_file_structured_retriever)

        self.chain = self.setup_chain(structured_retriever=retriever)

        final_response = self.chain.invoke(
            {
                "question": question,
                "kg": self.kg,
                "top_k": top_k,
                "next_chunk_limit" : next_chunk_limit
            }
        )
        return final_response
