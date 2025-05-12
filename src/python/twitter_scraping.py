from playwright.sync_api import sync_playwright
import time
from pprint import pprint
import json
import os
from datetime import datetime  # <-- NEW IMPORT
from pathlib import Path
import pandas as pd
import re
import urllib.parse
import logging
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)


file_dir = Path(__file__).resolve().parent
data_dir = file_dir/ ".." / "data"
tweet_dest_dir = data_dir / "tweets"
os.makedirs(tweet_dest_dir, exist_ok=True)
def scrape_all_tweet_texts(url: str, max_scrolls: int = 5):
    """
    Scrapes all tweet texts from a given Twitter URL by scrolling down.

    Args:
        url: The Twitter URL to scrape (e.g., a user profile or search results).
        max_scrolls: The maximum number of times to scroll down the page.

    Returns:
        A list of dicts with keys: username, tweetText, scrapeTime.
    """
    all_tweet_entries = []  
    seen_pairs = set()  # To keep track of unique (username, tweetText)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="twitter_auth.json", viewport={"width": 1280, "height": 1024})
        page = context.new_page()

        try:
            # logger.info(f"Navigating to {url}...")
            page.goto(url, wait_until='networkidle', timeout=60000)
            logger.info("Page loaded. Waiting for initial tweets...")

            try:
                page.wait_for_selector("[data-testid='tweet']", timeout=30000)
                logger.info("Initial tweets found.")
            except Exception as e:
                logger.info(f"Could not find initial tweets: {e}")
                try:
                    page.wait_for_selector("[data-testid='tweetText']", timeout=10000)
                    logger.info("Initial tweet text found.")
                except Exception as e2:
                    logger.error(f"Could not find initial tweet text either: {e2}")
                    page.screenshot(path="debug_screenshot_no_tweets.png")
                    return all_tweet_entries

            logger.info(f"Scrolling down {max_scrolls} times...")
            last_height = page.evaluate("document.body.scrollHeight")

            for i in range(max_scrolls):
                logger.info(f"Scroll attempt {i+1}/{max_scrolls}")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(3)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    logger.info("Reached bottom of page or no new content loaded.")
                    break
                last_height = new_height

                tweet_elements = page.query_selector_all("[data-testid='tweetText']")
                user_names = page.query_selector_all("[data-testid='User-Name']")
                now = datetime.now()

                for user, text in zip(user_names, tweet_elements):
                    username = user.text_content()
                    tweet_text = text.text_content()
                    if username and tweet_text:
                        key = (username, tweet_text)
                        if key not in seen_pairs:
                            seen_pairs.add(key)
                            all_tweet_entries.append({
                                "username": username,
                                "tweetText": tweet_text,
                                "scrapeTime": now.isoformat()
                            })

                logger.info(f"Total tweets collected so far: {len(all_tweet_entries)}")

        except Exception as e:
            logger.error(f"An error occurred during scraping: {e}")
        finally:
            logger.info("Closing browser.")
            browser.close()

    return all_tweet_entries

def transform_post_time(post_time, scrape_time):
    try:
        twitter_full_time_format = "%b %d, %Y"
        post_time_dt = pd.to_datetime(post_time, format=twitter_full_time_format, errors='coerce')
        
        if post_time_dt is not pd.NaT:
            pass
        elif 'h' in post_time:
            hour = int(post_time[:-1])
            post_time_dt =  scrape_time - pd.Timedelta(hours=hour)
        elif 'm' in post_time:
            minute = int(post_time[:-1])
            post_time_dt = scrape_time - pd.Timedelta(minutes=minute)
        elif 's' in post_time:
            second = int(post_time[:-1])
            post_time_dt = scrape_time - pd.Timedelta(seconds=second)
        else:
            current_year = scrape_time.year
            post_time = f"{current_year} {post_time}"
            post_time_dt = pd.to_datetime(post_time, format='%Y %b %d')

        if post_time_dt > pd.Timestamp.now():
            post_time_dt = post_time_dt - pd.DateOffset(years=1)
        return post_time_dt
    except Exception as e:
        logger.error(f"Error transforming post time: {e}")
        return pd.NaT
      

    
    
def scrape_tag(tag:str, max_scrolls:int = 5) -> pd.DataFrame:
    encoded = urllib.parse.quote(tag, safe='')
    target_url = f"https://x.com/search?q={encoded}&src=typeahead_click&f=live"
    
    tweet_data = scrape_all_tweet_texts(target_url, max_scrolls=max_scrolls)


    logger.info("\n--- Scraped Tweet Data ---")
    if tweet_data:
        pprint(tweet_data)
        logger.info(f"\nTotal unique tweet entries scraped: {len(tweet_data)}")
    else:
        logger.info("No tweet texts were scraped.")
        
    tweet_df = pd.DataFrame(tweet_data)
    tweet_df['scrapeTime'] = datetime.now()
    
    clean_tag = lambda x: re.sub(r'[^a-zA-Z0-9ก-๙]', '', x)
    tweet_df['tag'] = tag
    tweet_df['tag'] = tweet_df['tag'].apply(clean_tag)
    
    tweet_df['postTimeRaw'] = tweet_df['username'].str.split("·").str[-1]
    tweet_df['postTime'] = tweet_df.apply(lambda x: transform_post_time(x['postTimeRaw'], x['scrapeTime']), axis=1)
    tweet_df['postYear'] = tweet_df['postTime'].dt.year
    tweet_df['postMonth'] = tweet_df['postTime'].dt.month
    tweet_df['postDay'] = tweet_df['postTime'].dt.day
    
    tweet_tag_dest_dir = tweet_dest_dir / f"tag={tweet_df['tag'][0]}"
    os.makedirs(tweet_tag_dest_dir, exist_ok=True)
    tweet_df.to_parquet(tweet_tag_dest_dir, partition_cols=[ 'postYear', 'postMonth', 'postDay'], index=False, engine='pyarrow' ,existing_data_behavior='delete_matching')
    

    return tweet_df


if __name__ == "__main__":
    tag = "#ธรรมศาสตร์ช้างเผือก"
    scrape_tag(tag, 60)
    

