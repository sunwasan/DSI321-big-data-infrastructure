import os 
import sys 
from pathlib import Path
from pprint import pprint
import pandas as pd
from hashlib import sha256
from dotenv import load_dotenv
import os 
from tqdm import tqdm
import json
import logging
import re
load_dotenv()

GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY")
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY 

from google import genai
from google.genai import types


file_dir = Path(__file__).resolve().parent
# file_dir = Path(os.getcwd())
root_dir = file_dir / '..'
if Path("/data").exists():
    data_dir = Path("/data")
else:
    data_dir = root_dir / "data" 

tweets_dir = data_dir / "tweets"

hash_tag_dir = data_dir / "hash" 
hash_tag_dir.mkdir(parents=True, exist_ok=True)

faq_dir = data_dir / "faq"
faq_dir.mkdir(parents=True, exist_ok=True)

client = genai.Client(api_key=GEMINI_API_KEY)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

from pipeline.lakefs_load import to_faqs

# model = "gemini-2.5-flash-preview-04-17"
# or this
model = "gemini-2.0-flash"


def hash_string(s):
    return sha256(s.encode()).hexdigest()

def recall_processed(tag:str):
    tag = re.sub(r"[^a-zA-Z0-9ก-๙]", "", tag)
    existing_hashes_path = hash_tag_dir/ f"{tag}.txt"
    if existing_hashes_path.exists():
        with open(existing_hashes_path, "r") as f:
            existing_hashes = set(line.strip() for line in f)
    else:
        existing_hashes = set()
    return existing_hashes

def update_hash(tag:str, new_hashes:set, existing_hashes:set = None):
    tag = re.sub(r"[^a-zA-Z0-9ก-๙]", "", tag)
    existing_hashes_path = hash_tag_dir/ f"{tag}.txt"
    if not existing_hashes:
        existing_hashes = recall_processed(tag)
        
    unique_new_hashes = [h for h in new_hashes if h not in existing_hashes]

    with open(existing_hashes_path, "a") as f:
        for h in unique_new_hashes:
            f.write(f"{h}\n")


def get_tweet_data(tag:str, new_only:bool = True):
    tag = re.sub(r"[^a-zA-Z0-9ก-๙]", "", tag)

    tweets_tag_dir = tweets_dir / f"tag={tag}"
    all_parquet = list(tweets_tag_dir.rglob("*.parquet"))
    print(tweets_tag_dir)
    tweets_df = pd.concat([pd.read_parquet(f) for f in all_parquet], ignore_index=True)

    tweets_df.sort_values(by=['postTime'], ascending=True, inplace=True)
    tweets_df.drop_duplicates(subset="tweetText")
    tweets_df['index'] = tweets_df.index + 1
    tweets_df['postTime'] = tweets_df['postTime'].dt.strftime('%Y-%m-%d')
    
    if new_only:
        existing_hashes = recall_processed(tag)
        tweets_df['hash'] = tweets_df['tweetText'].apply(hash_string)
        new_tweets_df = tweets_df[~tweets_df['hash'].isin(existing_hashes)]
        return new_tweets_df
    
    
    return tweets_df


from prompt_template import instruction, prompt_template

def topic_extraction(
    tweets_dicts: list,
    faq_topic: set  = set()
    ) -> dict:
    
    prompt_formatted = prompt_template.format(
        faq_topic = faq_topic,
        messages="\n".join([f"{row['index']}: {row['tweetText']}" for row in tweets_dicts]),
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt_formatted,
        config=types.GenerateContentConfig(
            system_instruction=instruction,
            temperature=0.2, # low temperature for more deterministic output kub
        ),
    )
    response_text = response.text
    response_json = response_text[response_text.index("{"): response_text.rindex("}") + 1]
    response_json = response_json.replace("{{", "{").replace("}}", "}")
    response_json = json.loads(response_json, strict=False)
    return response_json

def extract(tag:str):
    tag = re.sub(r"[^a-zA-Z0-9ก-๙]", "", tag)
    tag = tag.lower()
    faq_tag_dir = faq_dir / f"tag={tag}"
    faq_tag_dir.mkdir(parents=True, exist_ok=True)
    
    faq_tag_dest = faq_tag_dir / f"part.parquet"

    tweets_df = get_tweet_data(tag)
    if tweets_df.empty:
        logger.info(f"No new tweets found for tag: {tag}")
        return None
    
    existing_faq_topics = set()
    if faq_tag_dest.exists():
        existing_faq_df = pd.read_parquet(faq_tag_dest)
        existing_faq_topics = set(existing_faq_df['topic'].explode().unique())
    
    tweets_dicts:list = tweets_df.to_dict(orient="records")
    step = 50
    prev_stop = 0
    all_response = []
    # new_topic = set(existing_faq_topics)

    for ind in tqdm(range(step, len(tweets_dicts) + step, step)):
        start = prev_stop
        stop = ind
        prev_stop = stop
        rows = tweets_dicts[start:stop]
        
        response = topic_extraction(rows, faq_topic=existing_faq_topics)
        
        for row in response['faq']:
            for topic in row['topic']:
                existing_faq_topics.add(topic)

        
        all_response.append(response['faq'])
        
    flatten_response =[ele for lst in all_response for ele in lst]
    new_faq = pd.DataFrame(flatten_response)\
            .merge(
                tweets_df[['index',  'postTime', 'scrapeTime']],
                on='index',
                how='left'
            )\
            .drop(columns=['index'])
    
    if faq_tag_dest.exists():
        existing_faq_df = pd.read_parquet(faq_tag_dest)
        existing_faq_df = existing_faq_df
        new_faq = pd.concat([existing_faq_df, new_faq], ignore_index=True)
        new_faq.drop_duplicates(subset=["text"], inplace=True)
        new_faq.reset_index(drop=True, inplace=True)
    new_faq['tag'] = tag
    new_faq['postDay'] = pd.to_datetime(new_faq['postTime']).dt.day
    new_faq['postMonth'] = pd.to_datetime(new_faq['postTime']).dt.month
    new_faq['postYear'] = pd.to_datetime(new_faq['postTime']).dt.year
    new_faq.to_parquet(
        path=faq_tag_dest,
        engine="pyarrow",
        compression="snappy",
        index=False,
    )

    new_hashes = set(tweets_df['tweetText'].apply(hash_string))
    update_hash(tag, new_hashes)
    logger.info(f"Updated hash for tag: {tag}")
    to_faqs(new_faq)
    return new_faq

if __name__ == "__main__":
    extract("DSI321")