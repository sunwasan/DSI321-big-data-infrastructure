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

# site:x.com inurl:/hashtag/ ธรรมศาสตร์

tags = [
    '#ธรรมศาสตร์ช้างเผือก',
]


@flow(name="scrape_tag_flow")
def scrape_tag_flow() -> None:
    """
    Flow to scrape tweets from a given tag.
    """
    for tag in tags:
        logger.info(f"Starting scrape for tag: {tag}")
        tweet_df = scrape_tag(tag)
        logger.info(f"Scrape completed for tag: {tag}")    
    
if __name__ == "__main__":
    scrape_tag_flow.serve(
        name = "scrape_tag_flow",
        cron = "*/15 * * * *", # every 15 minutes
        tags = ["scrape", "twitter"],
        description = "Flow to scrape tweets from a given tag.",
        
    )