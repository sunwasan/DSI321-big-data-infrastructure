import streamlit as st
import os
import sys
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import ast
# Constants and configurations
file_dir = Path(__file__).resolve().parent
print(f"Initial file_dir: {file_dir}")

# Set up paths based on environment
# Docker detection - check if we're in Docker
is_docker = Path("/data").exists() or os.path.exists("/.dockerenv")
print(f"Detected Docker environment: {is_docker}")

if is_docker:
    # Docker environment
    data_dir = Path("/data")
    config_dir = Path("/config")
    font_path = config_dir / "Sarabun-Regular.ttf"
    root_dir = Path(__file__).resolve().parent / ".."
    print("Using Docker paths")
else:
    # Local environment
    root_dir = file_dir / ".."
    data_dir = root_dir / "data"
    font_path = root_dir / "config" / "Sarabun-Regular.ttf"
    print("Using local paths")

faq_dir = data_dir / "faq"

# Check if paths exist
print(f"Root directory exists: {root_dir.exists()}")
print(f"Data directory exists: {data_dir.exists()}")
print(f"FAQ directory exists: {faq_dir.exists()}")
print(f"Font path exists: {os.path.exists(font_path)}")

# Fallback for font path if it doesn't exist
use_default_font = False
if not os.path.exists(font_path):
    print(f"Font not found at {font_path}, looking for alternatives...")
    possible_font_paths = [
        Path("config")  / "Sarabun-Regular.ttf",
    ]
    for path in possible_font_paths:
        if path.exists():
            font_path = path
            print(f"Found font at: {font_path}")
            break    
        else:
            print("Font not found, will use default font")
            use_default_font = True

# Make matplotlib use the font from font_path if available
if not use_default_font and os.path.exists(font_path):
    from matplotlib.font_manager import fontManager
    fontManager.addfont(str(font_path))
    plt.rcParams["font.family"] = "Sarabun"
else:
    print("Using default matplotlib font")

# Debug information
print(f"File directory: {file_dir}")
print(f"Root directory: {root_dir}")
print(f"Data directory: {data_dir}")
print(f"FAQ directory: {faq_dir}")
print(f"Font path: {font_path}")
print(f"Current working directory: {os.getcwd()}")




def load_faq_data(tag):
    """Load FAQ data for the selected tag."""
    faqs_dest = faq_dir / f"tag={tag}"
    print(f"Loading data from: {faqs_dest}")
    print(f"Current directory: {os.getcwd()}")
    
    # Debug information
    print(f"Does faq_dir exist? {faq_dir.exists()}")
    if faq_dir.exists():
        print(f"Contents of faq_dir: {list(faq_dir.glob('*'))}")
    
    print(f"Does tag directory exist? {faqs_dest.exists()}")
    if faqs_dest.exists():
        print(f"Contents of tag directory: {list(faqs_dest.glob('*'))}")
    
    if not faqs_dest.exists():
        st.warning(f"No data available for the selected tag. Path {faqs_dest} does not exist.")
        return None

    faqs_files = list(faqs_dest.glob("*.parquet"))
    print(f"Found parquet files: {faqs_files}")
    
    if not faqs_files:
        st.warning(f"No parquet files found in {faqs_dest}.")
        return None

    latest_file = sorted(faqs_files, key=lambda x: x.name)[-1]
    print(f"Using latest file: {latest_file}")
    return pd.read_parquet(latest_file)

def generate_word_cloud(text, stop_words, title):
    """Generate and display a word cloud."""
    try:
        # Set up WordCloud parameters
        word_cloud_params = {
            'stopwords': stop_words,
            'relative_scaling': 0.0,
            'min_font_size': 1,
            'background_color': "white",
            'max_words': 500,
            'colormap': "plasma",
            'scale': 10,
            'font_step': 1,
            'collocations': False,
            'regexp': r"[ก-๙a-zA-Z']+",
            'margin': 2,
        }
        
        # Add font path only if it's available
        if not use_default_font and os.path.exists(font_path):
            word_cloud_params['font_path'] = str(font_path)
            
        word_cloud = WordCloud(**word_cloud_params).generate(text)
        
    except Exception as e:
        st.error(f"Error generating word cloud: {str(e)}")
        print(f"WordCloud error: {str(e)}")
        # Fallback to basic word cloud without custom font
        word_cloud = WordCloud(
            background_color="white",
            max_words=100,
            stopwords=stop_words
        ).generate(text)

    plt.figure(figsize=(10, 5))
    plt.imshow(word_cloud, interpolation="bilinear")
    plt.axis("off")
    plt.title(title)
    st.pyplot(plt, clear_figure=True)

def generate_bar_chart(data, column, title, xlabel, ylabel):
    """Generate and display a bar chart."""
    data_count = (
        pd.DataFrame(data)
        .value_counts()
        .to_frame(name="count")
        .reset_index()
        .rename(columns={0: column})
        .sort_values(by="count", ascending=False)
        .head(10)
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(data_count[column], data_count["count"], color="skyblue")
    ax.invert_yaxis()
    for item, count in zip(data_count[column], data_count["count"]):
        ax.text(count - 1, item, str(count), va="center", ha="right", fontsize=10, color="white")

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    st.pyplot(fig, clear_figure=True)

# Streamlit app
def main():
    st.title("FAQ Data Visualization")
   
    tags = [t.split("=")[-1] for t in os.listdir(faq_dir)]
    tags = set(['เลือก Tag'] + tags)
    tag = st.selectbox("เลือก Tag", tags)

    if tag != "เลือก Tag":
        with st.spinner("กำลังโหลดข้อมูล..."):
            st.subheader("Word Cloud")

            faqs_df = load_faq_data(tag)
            if faqs_df is None:
                return

            stop_words = ["ธรรมศาสตร์", tag]

            # Process topics
            faqs_df['topic'] = faqs_df['topic'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

            topics = faqs_df["topic"].dropna().tolist()

            topics = [t for ele in topics for t in ele if not any(word in t for word in stop_words)]
            topics_text = " ".join(topics)

            # Process subtopics
            # faqs_df['subtopic'] = faqs_df['subtopic'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
            # subtopics = faqs_df["subtopic"].dropna().tolist()
            # subtopics = [s for ele in subtopics for s in ele if s not in stop_words]
            # subtopics_text = " ".join(subtopics)

            # Generate word clouds
            generate_word_cloud(topics_text, stop_words, "Word Cloud of FAQ Topics")
            # generate_word_cloud(subtopics_text, stop_words, "Word Cloud of FAQ Subtopics")

            st.subheader("Bar Chart")

            # Generate bar charts
            generate_bar_chart(topics, "topic", "Top 10 FAQ Topics", "Count", "Topic")
            # generate_bar_chart(subtopics, "subtopic", "Top 10 FAQ Subtopics", "Count", "Subtopic")

if __name__ == "__main__":
    main()
