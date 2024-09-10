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

    def _setup_partial_chain(self, structured_retriever):
        """
        Set up the prompt, template, and processing chain for answering questions.

        Args:
            structured_retriever (callable): A structured retriever to fetch context from the knowledge graph.
        """

        template = """Answer the question using the following context, if you are unsure say so.

        Question: {question}

        Context: {context}

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

    #A downside to langchain again, to combine the summary code and responses
    #We wanted to run code/summary in parallel via function call
    # Butthe function must take the same dict, so there is no way to differ the call
    #When running the chain. We must make two seperate functions that take same dict
    def _get_summary_response(self, _dict):
        """
        Get the response by invoking the chain with the question and relevant context.

        Args:
            _dict (dict): keys include
                question (str): The user's question.
                top_k (int): The number of top results to consider. Default is 1.

        Returns:
            str: The generated answer from the LLM.
        """

        #Could just pass the dict, but I want to be clear in setting default behavior
        #if called standalone 
        question = _dict.get("question") 
        top_k = _dict.get("top_k", 1) 

        retriever = dir_file_structured_retriever

        chain = self._setup_partial_chain(structured_retriever=retriever)

        response = chain.invoke(
            {
                "question": question,
                "kg": self.kg,
                "top_k": top_k,
            }
        )
        return response
    
    def _get_code_response(self, _dict):
        """
        Get the response by invoking the chain with the question and relevant context.

        Args:
            _dict (dict): keys include
                question (str): The user's question.
                top_k (int): The number of top results to consider. Default is 1.
                next_chunk_limit (int): The number of chunks to the left/right to search in the NEXT chain

        Returns:
            str: The generated answer from the LLM.
        """

        #Could just pass the dict, but I want to be clear in setting default behavior
        question = _dict.get("question") 
        top_k = _dict.get("top_k", 1) 
        next_chunk_limit = _dict.get("next_chunk_limit", 1) 

        retriever = code_structured_retriever

        chain = self._setup_partial_chain(structured_retriever=retriever)

        response = chain.invoke(
            {
                "question": question,
                "kg": self.kg,
                "top_k": top_k,
                "next_chunk_limit" : next_chunk_limit
            }
        )
        return response

    def get_full_response(self,  question, top_k: int = 1, next_chunk_limit: int = 1):
        """
        Get the response by invoking the chain with the question and relevant context.

        Args:
            question (str): The user's question.
            top_k (int): The number of top results to consider. Default is 1.
            next_chunk_limit (int): The number of chunks to the left/right to search in the NEXT chain

        Returns:
            str: The generated answer from the LLM.
        """

        template = """Answer the question by combining the two parital answers you are given.
        The two responses focus on either summary knowledge, or code specific knowledge.
        I would like for you to combine them to a single response that answers the question
        in detail. If there is not sufficient info say so.

        Question: {question}

        Summary response: {summary_response}

        Code response: {code_response}

        Answer:"""


        prompt = ChatPromptTemplate.from_template(template)



        chain = (
            RunnableParallel(
                {
                    "summary_response": RunnablePassthrough() | self._get_summary_response,
                    "code_response": RunnablePassthrough() | self._get_code_response,
                    "question": RunnablePassthrough(),
                }
            )
            | prompt
            | self.llm
            | StrOutputParser()
        )

        full_response = chain.invoke(
            {
                "question": question,
                "top_k": top_k,
                "next_chunk_limit" : next_chunk_limit
            }
        )

        return full_response
