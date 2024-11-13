import os
import time
from scrapy.crawler import CrawlerProcess  # type: ignore
from scrapy.utils.project import get_project_settings  # type: ignore
from scraper.spiders.spider import TextContentSpider  # type: ignore


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
        print(f"Time taken: {end_time - start_time} seconds")
