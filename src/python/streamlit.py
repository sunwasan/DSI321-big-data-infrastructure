import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import ast
# Constants and configurations
file_dir = Path(__file__).resolve().parent
root_dir = file_dir / ".."
data_dir = root_dir / "data"
faq_dir = data_dir / "faq"
font_path = root_dir / "config" / "Sarabun-Regular.ttf"
plt.rcParams['font.family'] = 'Tahoma'

# Helper functions
def load_faq_data(tag):
    """Load FAQ data for the selected tag."""
    faqs_dest = faq_dir / f"tag={tag}"
    if not faqs_dest.exists():
        st.warning("No data available for the selected tag.")
        return None

    faqs_files = list(faqs_dest.glob("*.csv"))
    if not faqs_files:
        st.warning("No data available for the selected tag.")
        return None

    latest_file = sorted(faqs_files, key=lambda x: x.name)[-1]
    return pd.read_csv(latest_file)

def generate_word_cloud(text, stop_words, title):
    """Generate and display a word cloud."""
    word_cloud = WordCloud(
        font_path=font_path,
        stopwords=stop_words,
        relative_scaling=0.0,
        min_font_size=1,
        background_color="white",
        max_words=500,
        colormap="plasma",
        scale=10,
        font_step=1,
        collocations=False,
        regexp=r"[ก-๙a-zA-Z']+",
        margin=2,
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

    tag = st.selectbox("เลือก Tag", ("เลือก Tag", "ธรรมศาสตร์ช้างเผือก"))

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

            topics = [t for ele in topics for t in ele if t not in stop_words]
            topics_text = " ".join(topics)

            # Process subtopics
            faqs_df['subtopic'] = faqs_df['subtopic'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
            subtopics = faqs_df["subtopic"].dropna().tolist()
            subtopics = [s for ele in subtopics for s in ele if s not in stop_words]
            subtopics_text = " ".join(subtopics)

            # Generate word clouds
            generate_word_cloud(topics_text, stop_words, "Word Cloud of FAQ Topics")
            generate_word_cloud(subtopics_text, stop_words, "Word Cloud of FAQ Subtopics")

            st.subheader("Bar Chart")

            # Generate bar charts
            generate_bar_chart(topics, "topic", "Top 10 FAQ Topics", "Count", "Topic")
            generate_bar_chart(subtopics, "subtopic", "Top 10 FAQ Subtopics", "Count", "Subtopic")

if __name__ == "__main__":
    main()
