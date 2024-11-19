import scrapy
import json
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from bs4 import BeautifulSoup
import re
import datetime
import hashlib
import os
import pandas
import uuid
from llama_index.embeddings.mistralai import MistralAIEmbedding


class TextContentSpider(CrawlSpider):
    name = "crawler"
    rules = (Rule(LinkExtractor(allow=()), callback="parse_response", follow=True),)

    def __init__(
        self,
        domain: str = "",
        depth: int = 1,
        db_path: str = "../data",
        *args,
        **kwargs,
    ):
        super(TextContentSpider, self).__init__(*args, **kwargs)
        self.allowed_domains = [domain]
        self.start_urls = [f"https://{domain}/"]
        self.depth_limit = int(depth)
        self.results = []
        self.status_counts = {}
        self.chunk_size = 1024
        self.db_path = db_path
        self.db_file = os.path.join(self.db_path, f"{domain}.json")
        self.embeddings_model = MistralAIEmbedding(
            api_key=os.getenv("MISTRAL_API_KEY"),
            model_name="mistral-embed",
        )
        self.embeddings_model_name = "mistral-embed"

        # browser config
        self.browser_headless = False

        self.load_database()

    def update_database(self):
        with open(self.db_file, "r") as file:
            db_data = json.load(file)
        file.close()
        with open(self.db_file, "w") as file:
            db_data["data"] = self.database.to_dict(orient="records")
            self.database = pandas.DataFrame(data=db_data["data"])
            json.dump(db_data, file, indent=4)
        file.close()

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, self.parse_response, meta={"depth": 0})

    def load_database(self):
        """
        here, it also depends if we want to take the chunk size in counts, i assume we just skip this
        """
        if os.path.exists(self.db_file):
            try:
                self.logger.info(f"Loading database from {self.db_file}")
                with open(self.db_file, "r") as file:
                    self.database = json.load(file)
                    self.database = pandas.DataFrame(data=self.database["data"])
                file.close()
            except:
                self.logger.info(f"Error loading database from {self.db_file}")
                self.database = pandas.DataFrame()
        else:
            self.logger.info(f"No database found at {self.db_file}, creating new one.")
            self.database = pandas.DataFrame(
                columns=[
                    "url",
                    "id",
                    "full_text",
                    "content_hash",
                    "chunked_text",
                    "last_time_crawled",
                    "status",
                ]
            )
            headers_ = {
                "url": [self.start_urls[0]],
                "time": str(datetime.datetime.now()),
                "config": {
                    "depth": self.depth_limit,
                    "chunk_size": self.chunk_size,
                    "embedding_model": self.embeddings_model_name,
                    "allowed_domains": [self.allowed_domains[0]],
                },
                "data": [],
            }
            with open(self.db_file, "w") as file:
                json.dump(headers_, file, indent=4)
            file.close()

    def parse_text(self, text: str):
        soup = BeautifulSoup(text, "html.parser")
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        clean_text = soup.get_text(separator=" ", strip=True)
        lines = [line.strip() for line in clean_text.splitlines()]
        cleaned_lines = [line for line in lines if line]
        cleaned_text = " ".join(cleaned_lines)

        return cleaned_text

    def get_embeddings(self, text: str, url: str) -> dict:
        chunks = self.chunk_text(text)
        embeddings = []
        embedeed_sentences = self.embeddings_model.encode(
            chunks
        ).tolist()  # Converted ndarray to list
        embeddings = [
            {
                "chunk_text": url + ": " + chunk,
                "embedding": embedeed_sentences[i],
                "id": str(uuid.uuid4()),
            }
            for i, chunk in enumerate(chunks)
        ]

        return {"embeddings": embeddings}

    def chunk_text(self, text: str) -> list:
        chunks = []
        current_chunk = ""
        sentences = re.split(r"(?<=[.!?]) +", text)
        for sentence in sentences:
            try:
                # f sentence in self.database['full_text'].values:
                if any(
                    sentence in text
                    for text in self.database["full_text"].values.tolist()
                ):
                    self.logger.warning(
                        f"Sentence already in database, skipping chunking."
                    )
                    continue
            except Exception:
                pass

            if len(current_chunk + sentence) <= self.chunk_size:
                current_chunk += sentence + " "
            else:
                if (
                    current_chunk.strip()
                ):  # Check if the current chunk is not empty before appending
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "

        if (
            current_chunk.strip()
        ):  # Check if the last chunk is not empty before appending
            chunks.append(current_chunk.strip())

        return chunks

    def parse_response(self, response):
        if response.meta.get("depth", 0) > self.depth_limit:
            self.logger.info(f"Reached depth limit for {response.url}")
            return
        if response.request.url != response.url:
            self.logger.info(
                f"Redirected from {response.request.url} to {response.url}"
            )

        status_code = str(response.status)
        if status_code not in self.status_counts:
            self.status_counts[status_code] = 0
        self.status_counts[status_code] += 1

        processed_text = self.parse_text(response.xpath("//body").extract_first())
        if len(processed_text) < 1:
            self.logger.info(f"Page is empty, try rendering it")
            return self.parse_response(response)
        else:
            self.logger.info(f"Page is not empty, continue")

        content_hash = hashlib.sha256(processed_text.encode("utf-8")).hexdigest()
        try:
            filtered_df = self.database[self.database["url"] == response.url]
            url_entry = filtered_df.iloc[0] if not filtered_df.empty else None
        except Exception as e:
            self.logger.error(f"Error accessing database entry: {str(e)}")
            url_entry = None

        # print(url_entry)
        if url_entry is not None:
            db_id = url_entry["id"]
            last_time_crawled = url_entry["last_time_crawled"]
            if url_entry["content_hash"] != content_hash:
                self.logger.info(
                    f"Content hash mismatch for {response.url}, updating entry."
                )
                self.database.loc[
                    self.database["url"] == response.url,
                    [
                        "full_text",
                        "content_hash",
                        "chunked_text",
                        "last_time_crawled",
                        "status",
                    ],
                ] = [
                    processed_text,
                    content_hash,
                    self.get_embeddings(processed_text, response.url),
                    last_time_crawled,
                    status_code,
                ]
            else:
                self.logger.info(f"URL {response.url} is already in the database.")
        else:
            self.logger.info(f"New URL {response.url}, adding to database.")
            new_entry = {
                "url": response.url,
                "id": str(uuid.uuid4()),
                "full_text": processed_text,
                "content_hash": content_hash,
                "chunked_text": self.get_embeddings(processed_text, response.url),
                "last_time_crawled": str(datetime.datetime.now()),
                "status": status_code,
            }
            self.database = pandas.concat(
                [self.database, pandas.DataFrame([new_entry])], ignore_index=True
            )

            self.update_database()

        links = LinkExtractor(allow=()).extract_links(response)
        for link in links:
            current_depth = response.meta.get("depth", 0)
            if current_depth < self.depth_limit:
                yield scrapy.Request(
                    link.url,
                    callback=self.parse_response,
                    meta={"depth": current_depth + 1},
                    errback=self.handle_error,
                )

    def handle_error(self, failure):
        if failure.value.response.status == 429:
            self.logger.error(
                f"Received 429 Too Many Requests from {failure.request.url}"
            )
            # Optionally, you can customize retry logic here

    def closed(self, reason):
        # self.update_database()
        with open(self.db_file, "w") as f:
            output_data = {
                "url": self.start_urls,
                "time": str(datetime.datetime.now()),
                "config": {
                    "depth": self.depth_limit,
                    "chunk_size": self.chunk_size,
                    "embedding_model": self.embeddings_model_name,
                    "allowed_domains": self.allowed_domains,
                },
                "data": self.database.to_dict(orient="records"),
            }
            json.dump(output_data, f, indent=4)
        self.logger.info(f"Closed spider with reason: {reason}")
        self.logger.info(f"Total requests sent: {len(self.results)}")
        self.logger.info(f"Status code counts: {self.status_counts}")
