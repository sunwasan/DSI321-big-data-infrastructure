from playwright.sync_api import sync_playwright
import time
from pprint import pprint
import json
import os
from datetime import datetime  # <-- NEW IMPORT

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
            print(f"Navigating to {url}...")
            page.goto(url, wait_until='networkidle', timeout=60000)
            print("Page loaded. Waiting for initial tweets...")

            try:
                page.wait_for_selector("[data-testid='tweet']", timeout=30000)
                print("Initial tweets found.")
            except Exception as e:
                print(f"Could not find initial tweets: {e}")
                try:
                    page.wait_for_selector("[data-testid='tweetText']", timeout=10000)
                    print("Initial tweet text found.")
                except Exception as e2:
                    print(f"Could not find initial tweet text either: {e2}")
                    page.screenshot(path="debug_screenshot_no_tweets.png")
                    return all_tweet_entries

            print(f"Scrolling down {max_scrolls} times...")
            last_height = page.evaluate("document.body.scrollHeight")

            for i in range(max_scrolls):
                print(f"Scroll attempt {i+1}/{max_scrolls}")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(3)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    print("Reached bottom of page or no new content loaded.")
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

                print(f"Total tweets collected so far: {len(all_tweet_entries)}")

        except Exception as e:
            print(f"An error occurred during scraping: {e}")
        finally:
            print("Closing browser.")
            browser.close()

    return all_tweet_entries


if __name__ == "__main__":
    # target_url = "https://x.com/search?q=%23DSI321&src=typed_query&f=live"
    target_url = "https://x.com/search?q=%23%E0%B8%98%E0%B8%A3%E0%B8%A3%E0%B8%A1%E0%B8%A8%E0%B8%B2%E0%B8%AA%E0%B8%95%E0%B8%A3%E0%B9%8C%E0%B8%8A%E0%B9%89%E0%B8%B2%E0%B8%87%E0%B9%80%E0%B8%9C%E0%B8%B7%E0%B8%AD%E0%B8%81&src=typeahead_click&f=live"
    print(f"Starting scrape for URL: {target_url}")
    tweet_data = scrape_all_tweet_texts(target_url, max_scrolls=10)

    print("\n--- Scraped Tweet Data ---")
    if tweet_data:
        pprint(tweet_data)
        print(f"\nTotal unique tweet entries scraped: {len(tweet_data)}")
    else:
        print("No tweet texts were scraped.")

    with open("scraped_tweets.json", "w", encoding="utf-8") as f:
        json.dump(tweet_data, f, indent=4, ensure_ascii=False)
    print("\nResults saved to scraped_tweets.json")
