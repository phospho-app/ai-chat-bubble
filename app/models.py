from loguru import logger
from scraper import (
    TextContentSpider,
)  # load the scraper from our scrapy project
from scrapy.crawler import CrawlerProcess  # type:ignore
from scrapy.utils.project import (  # type:ignore
    get_project_settings,
)
from qdrant_client import QdrantClient
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import StorageContext
from llama_index.embeddings.mistralai import MistralAIEmbedding
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
import time
import json
from mistralai import Mistral, AssistantMessage, ToolMessage
import os
import functools
from typing import Generator
from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel
import phospho

load_dotenv()

phospho.init()

# Check that the environment variables are set
assert os.getenv("MISTRAL_API_KEY"), "MISTRAL_API_KEY environment variable not set"


class QuestionOnUrlRequest(BaseModel):
    question: str


class ScraperInterface:
    """
    scraper logic:
    - scrapy project url LinkExtractor (basically a url follower, it will find all the urls in a page and then follow them)
    - export all the content to a json exporter, it will export the scraped data to a json file)
    - for the json format, check @json_format.py
    """

    def __init__(self, domain, depth):
        """
        Initialize the ScraperInterface with domain and depth.

        :param domain: The domain to scrape.
        :param depth: The depth of the crawl.
        """
        self.domain = domain
        self.depth = depth
        self.output_path = os.path.join(os.getcwd(), "data", f"{domain}.json")
        self.spider_db = os.path.join(os.getcwd(), "data")

    def run_crawler(self):
        """
        Run the Scrapy crawler to scrape the website.
        """
        print("Running crawler")
        start_time = time.time()
        process = CrawlerProcess(get_project_settings())
        process.crawl(
            TextContentSpider,
            domain=self.domain,
            depth=self.depth,
            output_path=self.output_path,
            db_path=self.spider_db,
        )
        process.start()  # Start the reactor and perform all crawls
        end_time = time.time()
        logger.info(f"Time taken: {end_time - start_time} seconds")


class EmbeddingsVS:
    def __init__(self, domain):
        """
        Initialize the EmbeddingsVS with domain.
        it's just some init variable so that we can modify easily which model or parameters to use

        :param domain: The domain to create embeddings for.
        """
        self.vector_db_name = domain.replace(".", "_")
        self.domain = domain
        self.embed_model = MistralAIEmbedding(
            model_name="mistral-embed", api_key=os.getenv("MISTRAL_API_KEY")
        )

        if os.getenv("QDRANT_API_KEY") and os.getenv("QDRANT_LOCATION"):
            logger.info("Connecting to Qdrant cloud")
            try:
                self.client = QdrantClient(
                    api_key=os.getenv("QDRANT_API_KEY"),
                    location=os.getenv("QDRANT_LOCATION"),
                )
            except Exception as e:
                logger.error(f"Failed to connect to Qdrant: {str(e)}")
                self.client = None
                logger.error(f"QDRANT_API_KEY: {os.getenv('QDRANT_API_KEY')}")
                logger.error(f"QDRANT_LOCATION: {os.getenv('QDRANT_LOCATION')}")
        else:
            logger.info("Connecting to Qdrant local")
            self.client = QdrantClient(
                # you can use :memory: mode for fast and light-weight experiments,
                # it does not require to have Qdrant deployed anywhere
                # but requires qdrant-client >= 1.1.1
                # location=":memory:"
                # otherwise set Qdrant instance address with:
                # url="http://<host>:<port>"
                # otherwise set Qdrant instance with host and port:
                host="qdrant",
                port=6333,
                # set API KEY for Qdrant Cloud
                # api_key=QDRANT_API_KEY,
            )
        self.scrapped_path = os.path.join(os.getcwd(), "data")
        self.limit = 5

    def upload_embeddings(self):
        """
        Upload the embeddings to the Qdrant vector database.
        """
        try:
            documents = SimpleDirectoryReader(self.scrapped_path).load_data()

            vector_store = QdrantVectorStore(
                client=self.client, collection_name=self.vector_db_name
            )
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                embed_model=self.embed_model,
            )
            logger.info(
                f"Uploaded {len(documents)} documents to {self.vector_db_name} collection"
            )

            return index
        except Exception as e:
            logger.error(f"Failed to upload embeddings: {str(e)}")

            raise e

    def search(self, query: str) -> List[dict]:
        """
        Search the vector database for the given query.

        :param query: The search query.
        :return: A dictionary of search results.
        """
        try:
            # Try to load existing index
            vector_store = QdrantVectorStore(
                client=self.client,
                collection_name=self.vector_db_name,
            )
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            index = VectorStoreIndex.from_vector_store(
                vector_store,
                storage_context=storage_context,
                embed_model=self.embed_model,
            )
        except Exception as _:
            logger.info(
                f"Collection {self.vector_db_name} not found. Creating new index."
            )
            index = self.upload_embeddings()

        # Perform the search
        retriever = index.as_retriever(similarity_top_k=self.limit)
        results = retriever.retrieve(query)

        results_embeddings = [
            {
                "id": node.metadata.get("id"),
                "text": node.text,
                "score": node.score if hasattr(node, "score") else None,
                "embeddings": node.metadata.get("embedding"),
                "url": node.metadata.get("url"),
            }
            for node in results
        ]

        logger.info("relevant urls: %s", [r["url"] for r in results_embeddings])
        return results_embeddings


class ChatMistral:
    def __init__(self, domain):
        """
        Initialize the ChatMistral with domain.

        :param domain: The domain to chat about.
        """
        self.domain = domain
        self.embeddings = EmbeddingsVS(domain)
        self.client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        self.model = "mistral-large-latest"
        self.temperature = 0.7
        self.names_to_functions = {
            "search_context": functools.partial(self.embeddings.search),
        }
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_context",
                    "description": f"Use this tool to get more context about what you don't know. This tool allows you to have access to all the data of the website {self.domain}",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to use for fetching data from the database",
                            }
                        },
                        "required": ["query"],
                    },
                },
            },
        ]

    def tools_to_str(tools_output: list) -> str:
        """
        Convert the tools output to a string.

        :param tools_output: The output from the tools.
        :return: A string representation of the tools output.
        """
        return "\n".join([tool["text"] for tool in tools_output])

    def search_context(self, query: str):
        """
        Search the context for the given query.

        :param query: The search query.
        :return: The search results.
        """
        results = self.embeddings.search(query)
        return results

    def chat(self, query: str) -> Generator[str, None, None]:
        """
        Chat with the Mistral model.
        It uses the official Mistral chat documentation with modifications to handle streaming tool calls.

        :param query: The chat query.
        :return: A generator yielding chat responses.
        """
        system_message = "You are a helpful assistant. Be straightforward and helpful. Keep your answers short and to the point. You answer in the language spoken to you."
        self.messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": query},
        ]
        chat_response = self.client.chat.stream(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature,
            tools=self.tools,
            tool_choice="any",
        )
        tool_call = False
        tool_call_data = None
        message_to_add = ""

        for data in chat_response:
            chunk = data.data.choices[0]
            if hasattr(chunk, "delta"):
                delta = chunk.delta
                if hasattr(delta, "tool_calls") and delta.tool_calls:
                    tool_call = True
                    if not tool_call_data:
                        tool_call_data = delta.tool_calls[0]
                        function_name = tool_call_data.function.name
                        function_args = tool_call_data.function.arguments
                if hasattr(delta, "content") and delta.content:
                    message_to_add += delta.content
                    yield delta.content
            elif hasattr(chunk, "content") and chunk.content:
                message_to_add += chunk.content
                yield chunk.content

            if tool_call:
                break

        if tool_call:
            print(f"tool call: {tool_call_data}")
            print(
                f"debug: appending message: {AssistantMessage(content=message_to_add, tool_calls=[tool_call_data])}"
            )
            self.messages.append(
                AssistantMessage(
                    content=message_to_add,
                    tool_calls=[tool_call_data],
                )
            )
            if isinstance(function_args, str):
                try:
                    function_args = json.loads(function_args)
                except json.JSONDecodeError:
                    yield "Error processing your request."
                    return
            function_result = self.names_to_functions[function_name](**function_args)
            function_result_text = ChatMistral.tools_to_str(function_result)
            self.messages.append(
                ToolMessage(
                    name=function_name,
                    content=function_result_text,
                    tool_call_id=tool_call_data.id,
                )
            )
            stream_response = self.client.chat.stream(
                model=self.model, messages=self.messages, temperature=self.temperature
            )
            final_response = ""
            for data in stream_response:
                chunk = data.data.choices[0]
                if (
                    hasattr(chunk, "delta")
                    and hasattr(chunk.delta, "content")
                    and chunk.delta.content
                ):
                    final_response += chunk.delta.content
                    yield chunk.delta.content
                elif hasattr(chunk, "content") and chunk.content:
                    final_response += chunk.content
                    yield chunk.content
            self.messages.append(AssistantMessage(content=final_response))
        else:
            self.messages.append(AssistantMessage(content=message_to_add))


class MainExecute:
    def __init__(self, domain: str, load: bool = True) -> None:
        """
        Initialize the MainExecute class.
        """
        self.domain = domain
        depth = 2
        self.load = load
        self.scraper = ScraperInterface(domain=domain, depth=depth)  # scrape first
        self.embeddings = EmbeddingsVS(domain=domain)  # then upload the embeddings
        self.chat = ChatMistral(domain=domain)  # then create the chat

        if self.load:
            self.scraper.run_crawler()  # run the scraper
            logger.info("Finished scraping.")
            self.embeddings.upload_embeddings()  # upload the embeddings
            logger.info("Finished uploading embeddings.")

    def ask(self, question: str):
        """
        Ask a question to the chatbot based on a url.
        """
        try:
            output = ""
            # Stream the response
            for chunk in self.chat.chat(question):
                output += chunk
                yield chunk  # Continue yielding chunks as they arrive

            # Log the input and output using phospho
            phospho.log(input=question, output=output)

        except KeyboardInterrupt:
            logger.info("Exiting program.")
