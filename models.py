from loguru import logger
from scraper import (
    TextContentSpider,
)  # load the scraper from our scrapy project
from scrapy.crawler import CrawlerProcess  # type:ignore
from scrapy.utils.project import (  # type:ignore
    get_project_settings,
)
from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer
import time
import json
from mistralai import Mistral, AssistantMessage, ToolMessage
import os
import functools
from typing import Generator
from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel


load_dotenv()

# Check that the environment variables are set
assert os.getenv("QDRANT_LOCATION"), "QDRANT_LOCATION environment variable not set"
assert os.getenv("QDRANT_API_KEY"), "QDRANT_API_KEY environment variable not set"
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
        self.output_path = f"data/{self.domain}.json"
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
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.qdrant_client = QdrantClient(
            os.getenv("QDRANT_LOCATION"),
            api_key=os.getenv("QDRANT_API_KEY"),
        )  # here if you want to change the location of the vectorstore
        self.scrapped_path = f"data/{self.domain}.json"
        self.limit = 5

    def upload_embeddings(self):
        """
        Upload the embeddings to the Qdrant vector database.
        """

        with open(self.scrapped_path, "r") as file:
            documents = json.load(file)
        file.close()

        # create collection if not exist
        if not self.qdrant_client.collection_exists(self.vector_db_name):
            self.qdrant_client.create_collection(
                collection_name=self.vector_db_name,
                vectors_config=models.VectorParams(
                    size=self.encoder.get_sentence_embedding_dimension(),  # Vector size is defined by used model
                    distance=models.Distance.COSINE,  # change the search methods as you want
                ),
                # TODO: add on_disk_payloads=True, if you have a lot of data (will be slower)
            )
        self.qdrant_client.upload_points(
            collection_name=self.vector_db_name,
            points=[
                models.PointStruct(
                    id=chunk["id"],
                    vector=chunk["embedding"],
                    payload={
                        "chunk_text": chunk["chunk_text"],
                        "embeddings": chunk["embedding"],
                        "url": documents["data"][idx]["url"],
                    },
                )
                for idx, doc in enumerate(documents["data"])
                for chunk in doc["chunked_text"]["embeddings"]
            ],
        )
        logger.info(
            f"Uploaded {len(documents['data'])} documents to {self.vector_db_name} collection"
        )

    def search(self, query: str) -> List[dict]:
        """
        Search the vector database for the given query.

        :param query: The search query.
        :return: A dictionary of search results.
        """
        if not self.qdrant_client.collection_exists(self.vector_db_name):
            logger.info(
                f"Collection {self.vector_db_name} not found. Attempting to create."
            )
            self.upload_embeddings()  # Ensure the collection is created
        hits = self.qdrant_client.search(
            collection_name=self.vector_db_name,
            query_vector=self.encoder.encode(query).tolist(),
            limit=self.limit,
            with_payload=True,  # Ensure payload containing embeddings is returned
        )
        results_qdrant_embeddings = [
            {
                "id": hit.id,
                "text": hit.payload["chunk_text"],
                "score": hit.score,
                "embeddings": hit.payload["embeddings"],
                "url": hit.payload["url"],
            }
            for hit in hits
        ]

        logger.info("relevant urls: %s", [r["url"] for r in results_qdrant_embeddings])
        return results_qdrant_embeddings


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
            for chunk in self.chat.chat(question):
                yield chunk

        except KeyboardInterrupt:
            logger.info("Exiting program.")
