from prefect import flow, task
from pathlib import Path
from datetime import datetime
import logging 
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

file_dir = Path(__file__).resolve().parent
sys.path.append(str(file_dir))


from twitter_scraping import scrape_tag
from faqs_extraction import process
# site:x.com inurl:/hashtag/ ธรรมศาสตร์

tags = [
    '#ธรรมศาสตร์ช้างเผือก',
]


@flow(name="scrape_tag_flow")
def scrape_tag_flow() -> None:
    @task 
    def scrape_tag(tag: str, max_tweets: int) -> None:
        """
        Task to scrape tweets from a given tag.
        """
        logger.info(f"Scraping tweets for tag: {tag}")
        scrape_tag(tag, max_tweets)
        logger.info(f"Scraping completed for tag: {tag}")
    @task 
    def faq_extract(tag: str) -> None:
        """
        Task to extract FAQ from tweets.
        """
        logger.info(f"Extracting FAQ for tag: {tag}")
        process(tag)
        logger.info(f"FAQ extraction completed for tag: {tag}")
    
    
    """
    Flow to scrape tweets from a given tag.
    """
    for tag in tags:
        logger.info(f"Starting scrape for tag: {tag}")
        scrape_tag(tag, 3)
        logger.info(f"Scrape completed for tag: {tag}")    
        faq_extract(tag)
        logger.info(f"FAQ extraction completed for tag: {tag}")
    
if __name__ == "__main__":
    scrape_tag_flow.serve(
        name = "scrape_tag_flow",
        cron = "*/15 * * * *", # every 15 minutes
        tags = ["scrape", "twitter"],
        description = "Flow to scrape tweets from a given tag.",
        
    )