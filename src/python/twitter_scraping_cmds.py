# pip install playwright scrapfly-sdk
# playwright install 

from playwright.sync_api import sync_playwright
from pprint import pprint
import json

def scrape_twitter_info(url: str, boolean_user):

    _xhr_calls = []

    def intercept_response(response):
        if response.request.resource_type == "xhr":
            _xhr_calls.append(response)
        return response
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width":1920, "height":1080})
        page = context.new_page()

        page.on("response", intercept_response)

        page.goto(url)

        if boolean_user:
            selector = "[data-testid='primaryColumn']"
            xhr_condition = "UserBy"
            json_condition = "user"
        else:
            selector = "[data-testid='tweet']"
            xhr_condition = "TweetResultByRestId"
            json_condition = "tweetResult"

        # [data-testid='primaryColumn'] - userprofile data
        # [data-testid='tweet'] - tweets
        page.wait_for_selector(selector)
        # TweetResultByRestId
        usercalls = [f for f in _xhr_calls if xhr_condition in f.url]
        for uc in usercalls:
            data = uc.json()
            # tweetResult
            return data['data'][json_condition]['result']
        
# pprint(scrape_profile_info("https://x.com/MrBeast"))

with open("mr_beast_user_post_info.json", "w") as f:
    json.dump(scrape_twitter_info("https://x.com/MrBeast/status/1874500952046338435", False), f,indent=4)


