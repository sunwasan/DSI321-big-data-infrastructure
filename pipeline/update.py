import logging
from pathlib import Path
import hashlib
import sys
import os
import re
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

def setup_paths():
    file_dir = Path(__file__).parent
    sys.path.append(str(file_dir))

    if Path('data/').exists():
        data_dir = Path('data/')
    else:
        data_dir = file_dir / ".." / "data"

    tweet_dest_dir = data_dir / "tweets"
    return tweet_dest_dir

tweet_dest_dir = setup_paths()

from x_scrap import *


def clean_tag(tag):
    return re.sub(r'[^a-zA-Z0-9ก-๙]', '', tag)

def get_existing_partitions(tag_dir, years, months, days):
    all_existing_partitions = []
    for year in years:
        for month in months:
            for day in days:
                partition = f"postYear={year}/postMonth={month}/postDay={day}"
                full_path = tag_dir / partition
                if full_path.exists():
                    all_existing_partitions.append(full_path)
    return all_existing_partitions

def update_tag(tag: str, max_scrolls: int = 1):
    try:
        tag_clean = clean_tag(tag)
        tag_clean = tag_clean.lower()
        logging.info(f"Scraping tag: {tag} (clean: {tag_clean}) with max_scrolls={max_scrolls}")

        scraped_df = scrape_tag(tag, max_scrolls=max_scrolls)
        scraped_df = scraped_df.set_index(["tweetText", "postTime"])
        tag_dir = tweet_dest_dir / f"tag={tag_clean}"

        if not os.path.exists(tag_dir):
            os.makedirs(tag_dir)
            logging.info(f"Created directory: {tag_dir}")

        all_year = scraped_df['postYear'].unique()
        all_month = scraped_df['postMonth'].unique()
        all_day = scraped_df['postDay'].unique()

        all_existing_partitions = get_existing_partitions(tag_dir, all_year, all_month, all_day)

        if len(all_existing_partitions) == 0:
            updated_df = scraped_df.copy()
            logging.info("No existing partitions found. Using scraped data as updated data.")
        else:
            all_parquets_paths = [p for p_files in all_existing_partitions for p in p_files.glob("*.parquet")]

            existed_df = pd.concat([pd.read_parquet(p) for p in all_parquets_paths], ignore_index=True)
            existed_df = existed_df.set_index(["tweetText", "postTime"])

            new_text = list(set(scraped_df.index) - set(existed_df.index))
            new_df = scraped_df.loc[new_text]

            updated_df = pd.concat([existed_df, new_df])
            logging.info(f"Found {len(new_df)} new tweets to add.")
            
        updated_df.reset_index(inplace=True)
        updated_df['scrapeTime'] = pd.to_datetime(updated_df['scrapeTime'])
        updated_df['postTime'] = updated_df.apply(
            lambda row: transform_post_time(row['postTimeRaw'], row['scrapeTime']), axis=1)
        updated_df['postDay'] = updated_df['postTime'].dt.day
        updated_df['postMonth'] = updated_df['postTime'].dt.month
        updated_df['postYear'] = updated_df['postTime'].dt.year
        print(updated_df.head())
        updated_df.to_parquet(
            partition_cols=["postYear", "postMonth", "postDay"],
            path=tag_dir,
            engine="pyarrow",
            compression="snappy",
            # index=False,
            existing_data_behavior="delete_matching"
        )
        logging.info(f"Updated parquet files written to {tag_dir}")

    except Exception as e:
        logging.error(f"Error updating tag '{tag}': {e}", exc_info=True)
        
if __name__ == "__main__":
    update_tag(
        tag="DSI321",
        max_scrolls=1
    )