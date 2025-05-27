from lakefs.client import Client
import lakefs
from lakefs import repositories
import subprocess
import pandas as pd
from dotenv import load_dotenv
import os
import shutil

from pathlib import Path
import sys 

file_dir = Path(__file__).resolve().parent
sys.path.append(str(file_dir))

if Path('data/').exists():
    data_dir = Path('data/')
else:
    data_dir = file_dir / ".." / "data"
    
    

import os

# LakeFS settings
lakefs_endpoint = "http://lakefsdb:8000" 
access_key = "access_key" 
secret_key = "secret_key"
repo = "social-listening"
branch = "main"

local_dir = data_dir

storage_options = {
    "key": access_key,
    "secret": secret_key,
    "client_kwargs": {
        "endpoint_url": lakefs_endpoint,
    }
}
import pandas as pd 

def to_lakefs(df, collection):
    """
    Save DataFrame to LakeFS S3 with partitioning.
    """
    lakefs_s3_tweets_path = f"s3://{repo}/{branch}/{collection}/"
    df.to_parquet(
        lakefs_s3_tweets_path,
        storage_options=storage_options,
        engine="pyarrow",
        existing_data_behavior="delete_matching",
        partition_cols=["tag", "postYear", "postMonth", "postDay"],
    )
    
def to_tweets(df):
    """
    Save DataFrame to local tweets directory with partitioning.
    """    
    to_lakefs(df, "tweets")
    
def load_tweets():
    """
    Load tweets from the local directory and save to LakeFS.
    """
    tweets_dir = data_dir / "tweets"
    all_tag_dirs = os.listdir(tweets_dir)
    all_tag_dirs = [os.path.join(tweets_dir, tag) for tag in all_tag_dirs]
    
    for tag_dir in all_tag_dirs:
        tag_df = pd.read_parquet(tag_dir)
        to_tweets(tag_df)
        
def to_faqs(df):
    """
    Save DataFrame to LakeFS S3 with partitioning for FAQs.
    """
    to_lakefs(df, "faq")
    
def load_faqs():
    """
    Load FAQs from the local directory and save to LakeFS.
    """
    faqs_dir = data_dir / "faq"
    all_faqs_files = os.listdir(faqs_dir)
    all_faqs_files = [os.path.join(faqs_dir, faq) for faq in all_faqs_files]
    
    for faq_file in all_faqs_files:
        faq_df = pd.read_parquet(faq_file)
        to_faqs(faq_df)    


# if __name__ == "__main__":
#     tweets_dir = data_dir / "tweets"
#     all_tag_dir = os.listdir(tweets_dir)
#     all_tag_dir = [os.path.join(tweets_dir, tag) for tag in all_tag_dir]
#     for tag_dir in all_tag_dir:
#         tag_df = pd.read_parquet(tag_dir)
#         to_staging(tag_df)
        

#     print("Load tweets done!")

if __name__ == "__main__":
    load_faqs()

