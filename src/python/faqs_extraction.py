import os 
import sys 
from pathlib import Path
from pprint import pprint
import pandas as pd
from hashlib import sha256
from dotenv import load_dotenv
import os 
from tqdm import tqdm
load_dotenv()

GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY")
os.environ["GEMINI_API_KEY "] = GEMINI_API_KEY 

from google import genai
from google.genai import types


file_dir = Path(__file__).resolve().parent
root_dir = file_dir / '..'
data_dir = root_dir / "data" 
tweets_dir = data_dir / "tweets"


faq_dir = data_dir / "faq"
faq_dir.mkdir(parents=True, exist_ok=True)

issue_dir = data_dir / "issue"
issue_dir.mkdir(parents=True, exist_ok=True)

client = genai.Client(api_key=GEMINI_API_KEY)

def hash_string(s):
    return sha256(s.encode()).hexdigest()

def recall_processed_hashes(
    tag:str,
):
    """ 
    This function reads the processed hashes from a file and returns them as a set.
    Args:
        tag (str): The tag to identify the processed hashes file.
    Returns:
        set: A set of processed hashes.
    """
    processed_record_path = data_dir / "processed_hashes" / tag 
    processed_hashes = set()
    if processed_record_path.exists():
        processed_hashes = set(processed_record_path.read_text().splitlines())
    return processed_hashes

def save_processed_hashes(
    tag:str,
    hashes:set,
):
    """
    This function saves the processed hashes to a file.
    Args:
        tag (str): The tag to identify the processed hashes file.
        hashes (set): A set of processed hashes to save.
    """
    processed_record_path = data_dir / "processed_hashes" / tag 
    processed_record_path.parent.mkdir(parents=True, exist_ok=True)
    processed_record_path.write_text("\n".join(hashes))
    logger.info(f"Processed hashes saved to {processed_record_path}")


def load_tweets_df(
    tag:str,
    only_new : bool = True
) -> pd.DataFrame: :
    tweets_tag_dir = tweets_dir / f"tag={tag}"
    all_parquet = list(tweets_tag_dir.rglob("*.parquet"))
    
    tweets_tag_dir = tweets_dir / f"tag={tag}"
    all_parquet = list(tweets_tag_dir.rglob("*.parquet"))
    tweets_df = pd.concat([pd.read_parquet(f) for f in all_parquet], ignore_index=True)
    
    tweets_df.sort_values(by=['postTime'], ascending=True, inplace=True)
    tweets_df.drop_duplicates(subset="tweetText")
    tweets_df['index'] = tweets_df.index + 1
    tweets_df['postTime'] = tweets_df['postTime'].dt.strftime('%Y-%m-%d')
    
    if only_new:
        tweets_df = tweets_df[tweets_df['postTime'] == pd.Timestamp.now().strftime('%Y-%m-%d')]
        processed_hashes = recall_processed_hashes(tag)
        file_hashes = (tweets_df['tweetText'] + tweets_df['postTime'].astype(str)).apply(hash_string)
        tweets_df['hash'] = file_hashes
        tweets_df = tweets_df[~tweets_df['hash'].isin(processed_hashes)]
        tweets_df.drop(columns=['hash'], inplace=True)
        tweets_df.reset_index(drop=True, inplace=True)
        
    return tweets_df

def extract_faqs(
    tweets_dicts:list,
) -> dict:    
               
    instruction = """
    คุณทำหน้าที่ในฝ่ายประชาสัมพันธ์ของมหาวิทยาลัย เป้าหมายของคุณคือการรวบรวมและจัดกลุ่ม 
    "คำถามที่พบบ่อย" (FAQ) หรือ "ปัญหาที่พบบ่อย" (Issue) จากโซเชียลมีเดีย 
    เพื่อใช้ในการตัดสินใจว่าควรสื่อสารผ่าน PR หรือรายงานต่อหน่วยงานที่เกี่ยวข้อง
    โดยปัญหา / คำถามที่นำมาจัดกลุ่มจะต้องเกี่ยวข้องและแก้ไขได้ในระดับมหาวิทยาลัย
    คุณจะได้รับข้อความจากโซเชียลมีเดียที่เกี่ยวข้องกับมหาวิทยาลัย

    คำแนะนำในการจัดกลุ่ม:
    1. **ระบุประเภท**: แยกระหว่าง "คำถาม" (faq) และ "ปัญหา" (issue)
    - คำถาม (faq): ข้อความที่ผู้ใช้ต้องการข้อมูลหรือคำแนะนำ / ประโยคคำถาม **ต้องเป็นคำถามที่ทางมหาวิทยาลัยสามารถตอบได้** และ เกี่ยวข้องกับทางมหาวิทยาลัยโดยตรง
    - ปัญหา (issue): ข้อความที่ผู้ใช้ระบุถึงความไม่พึงพอใจหรือสิ่งที่ต้องแก้ไข **ต้องเป็นปัญหาที่ทางมหาวิทยาลัยสามารถแก้ไขได้** และ เกี่ยวข้องกับทางมหาวิทยาลัยโดยตรง

    2. **ระบุหมวดหมู่ (topic)**:
    - ใช้หมวดหมู่ที่มีอยู่แล้วหากข้อความใหม่เข้ากับหมวดหมู่เดิม
    - สร้างหมวดหมู่ใหม่เมื่อไม่มีหมวดหมู่เดิมที่เหมาะสม
    - ตั้งชื่อหมวดหมู่ให้กระชับ เข้าใจง่าย และมีความเฉพาะเจาะจงในระดับที่เหมาะสม
    - ข้อความหนึ่งสามารถอยู่ได้หลายหมวดหมู่หากมีความเกี่ยวข้อง
    - ต้องเกี่ยวข้องกับทางมหาวิทยาลัยโดยตรง และสามารถแก้ไขได้ในระดับมหาวิทยาลัย

    3. **ระบุหมวดหมู่ย่อย (subtopic)**:
    - ระบุหมวดหมู่ย่อยที่มีความเฉพาะเจาะจงมากขึ้น
    - สามารถมีได้หลายหมวดหมู่ย่อยต่อหนึ่งข้อความ
    - หมวดหมู่ย่อยควรให้รายละเอียดเพิ่มเติมที่เป็นประโยชน์เกี่ยวกับคำถามหรือปัญหานั้น ๆ
    - ต้องเกี่ยวข้องกับทางมหาวิทยาลัยโดยตรง และสามารถแก้ไขได้ในระดับมหาวิทยาลัย

    4. **พิจารณาเฉพาะข้อความที่เกี่ยวข้อง**:
    - พิจารณาเฉพาะข้อความที่เป็นคำถามหรือปัญหาเท่านั้น
    - ข้อความทั่วไป ข้อความสนทนา หรือข้อความที่ไม่มีเนื้อหาเป็นคำถามหรือปัญหา ไม่ต้องนำมาจัดกลุ่ม

    ตอบกลับมาในรูปแบบ JSON โดยมีโครงสร้างดังนี้:
    {
        "issue": [
            {"index": 1, "text": "ข้อความ", "topic": ["หมวดหมู่1", "หมวดหมู่2"], "subtopic": ["หมวดย่อย1", "หมวดย่อย2"]},
            {"index": 2, "text": "ข้อความ", "topic": ["หมวดหมู่1"], "subtopic": ["หมวดย่อย1"]}
        ],
        "faq": [
            {"index": 1, "text": "ข้อความ", "topic": ["หมวดหมู่1"], "subtopic": ["หมวดย่อย1", "หมวดย่อย2"]},
            {"index": 2, "text": "ข้อความ", "topic": ["หมวดหมู่1", "หมวดหมู่2"], "subtopic": ["หมวดย่อย1"]}
        ]
    }

    หากไม่มีคำถามหรือปัญหาที่เกี่ยวข้อง ให้ส่งคืนค่าเป็น empty array ในหมวดนั้น
    """

    prompt_template = """
    # topic ของคำถามที่พบบ่อยในอดีต (FAQ) - ใช้เป็นตัวอย่างในการจัดกลุ่ม:
    {faq_topic}

    # sub topic ของคำถามที่พบบ่อยในอดีต (FAQ) - ใช้เป็นตัวอย่างในการจัดกลุ่ม:
    {faq_subtopic}

    # topic ของปัญหาที่พบบ่อยในอดีต (Issue) - ใช้เป็นตัวอย่างในการจัดกลุ่ม:
    {issue_topic}

    # sub topic ของปัญหาที่พบบ่อยในอดีต (Issue) - ใช้เป็นตัวอย่างในการจัดกลุ่ม:
    {issue_subtopic}

    # ตัวอย่างการจัดกลุ่ม:
    text: 'ไฟล์สมัครในเว็บมธ.อยู่ตรงไหนเหรอคะ มีใครพอจะทราบไหมคะ' 
    topic: ['สอบถามเอกสาร']
    subtopic: ['เอกสารการสมัคร', 'การเข้าถึงข้อมูล']

    text: 'หอในเปิดปิดกี่โมง มีเคอร์ฟิวไหม แล้วถ้าเข้าหอดึกต้องทำยังไงบ้าง'
    topic: ['หอพัก']
    subtopic: ['กฎระเบียบหอพัก', 'เวลาเปิด-ปิด']

    text: 'ระบบลงทะเบียนล่มอีกแล้ว ทำไมเกิดปัญหาทุกเทอมเลย'
    topic: ['ระบบลงทะเบียน', 'ปัญหาเทคนิค']
    subtopic: ['ระบบล่ม', 'ความเสถียรของระบบ']

    # ข้อความที่ต้องการจัดกลุ่ม:
    {messages}

    โปรดวิเคราะห์และจัดกลุ่มข้อความตามคำแนะนำที่ให้ไว้ และส่งคืนเป็น JSON ตามรูปแบบที่กำหนด
    """
    
    def topic_extraction(
        tweets_dicts: list,
        faq_topic: str = faq_topic,
        faq_subtopic: str = faq_subtopic,
        issue_topic: str = issue_topic,
        issue_subtopic: str = issue_subtopic
        ) -> dict:
        
        prompt_formatted = prompt_template.format(
            faq_topic = faq_topic,
            faq_subtopic = faq_subtopic,
            issue_topic = issue_topic,
            issue_subtopic = issue_subtopic,
            messages="\n".join([f"{row['index']}: {row['tweetText']}" for row in tweets_dicts]),
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
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
    
    step = 50
    prev_stop = 0
    all_response = []
    for ind in tqdm(range(step, len(df_dict) + step, step)):
        start = prev_stop
        stop = ind
        prev_stop = stop
        rows = df_dict[start:stop]
        
        response = topic_extraction(rows)
        
        for row in response['issue']:
            for topic in row['topic']:
                issue_topic.add(topic)
            for subtopic in row['subtopic']:
                issue_subtopic.add(subtopic)
        for row in response['faq']:
            for topic in row['topic']:
                faq_topic.add(topic)
            for subtopic in row['subtopic']:
                faq_subtopic.add(subtopic)
        
        all_response.append(response)
        
    return all_response

def process(
    tag:str,
    only_new:bool = True,
) -> None:
    """
    Main function to process tweets and extract FAQs and issues.
    Args:
        tag (str): The tag to identify the tweets.
        only_new (bool): Whether to process only new tweets. Default is True.
    """
    tweets_df = load_tweets(tag, only_new)
    tweets_dicts = tweets_df[['postTime', 'tweetText', 'index']].to_dict(orient='records')

    if not tweets_dicts:
        print("No new tweets to process.")
        return
    
    all_response = extract_faqs(tweets_dicts)
    today = pd.Timestamp.now().strftime("%Y-%m-%d")

    faqs = [faq for response in all_response for faq in response['faq']  ]
    faqs_df = pd.DataFrame(faqs)
    faqs_df = faqs_df.merge(
        df[['index', 'postTime']],
        how='left',
        on='index'
    )

    issues = [issue for response in all_response for issue in response['issue']]
    issues_df = pd.DataFrame(issues)
    issues_df = issues_df.merge(
        df[['index', 'postTime']],
        how='left',
        on='index'
    )
    
    faqs_dest = faq_dir / f"tag={tag}" / f"{today}.csv"
    issues_dest = issue_dir / f"tag={tag}" / f"{today}.csv"
    
    append = os.path.exists(faqs_dest)
    faqs_df.to_csv(faqs_dest, mode='a', header=not append, index=False)
    
    append = os.path.exists(issues_dest)
    issues_df.to_csv(issues_dest, mode='a', header=not append, index=False)
        
    processed_record = tweets_df['tweetText'] + tweets_df['postTime'].astype(str)
    processed_record = processed_record.apply(hash_string)
    processed_record_set = set(processed_record)
    save_processed_hashes(tag, processed_record_set)
    logger.info(f"Processed {len(processed_record_set)} tweets for tag: {tag}")    

