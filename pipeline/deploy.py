from prefect import flow, task
from pathlib import Path
from datetime import datetime, timedelta
from prefect.schedules import Interval

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

from update import update_tag
from extraction import extract
# site:x.com inurl:/hashtag/ ธรรมศาสตร์

tags = [
    '#ธรรมศาสตร์ช้างเผือก',
    '#DSI321'
]


@flow(name="scrape_tag_flow")
def scrape_tag_flow() -> None:       
    for tag in tags:
        logger.info(f"Starting scrape for tag: {tag}")
        update_tag(tag, max_scrolls=1)
        logger.info(f"Finished scrape for tag: {tag}")  
        extract(tag)
        logger.info(f"Finished extract for tag: {tag}")
    
if __name__ == "__main__":
    scrape_tag_flow.from_source(
        source=Path(__file__).parent, 
        entrypoint="./deploy.py:scrape_tag_flow",
    ).deploy(
        name="scrape_tag_flow",
        tags=["scrape", "tag"],
        schedule=Interval(
            timedelta(minutes=15),
            timezone="Asia/Bangkok",
        ),
        work_pool_name= "default-agent-pool",
    )
