import streamlit as st
import requests
import time
import pandas as pd
import psycopg2
import os
import matplotlib.pyplot as plt
import random
from huggingface_hub import InferenceClient
from transformers import AutoTokenizer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airflow API URL
AIRFLOW_TRIGGER_URL = "http://localhost:8080/api/v1/dags/youtube_comments_etl_pipeline/dagRuns"
AIRFLOW_DAG_STATUS_URL = "http://localhost:8080/api/v1/dags/youtube_comments_etl_pipeline/dagRuns/"

# Hugging Face API
HF_TOKEN = os.getenv("TestHFToken")
MODEL_NAME = "nlptown/bert-base-multilingual-uncased-sentiment"  # More reliable model

# Initialize client only if token is available
if HF_TOKEN:
    client = InferenceClient(model=MODEL_NAME, token=HF_TOKEN)
else:
    st.warning("⚠️ Hugging Face token not found. Using mock sentiment analysis.")
    client = None

# Streamlit UI Title
st.set_page_config(page_title="YouTube Sentiment Analysis", layout="wide")
st.title("🎬 YouTube Comments Sentiment Analysis")

# Pin the title at the top using markdown and CSS
st.markdown(
    """
    <style>
    .title {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: white;
        padding: 10px 0;
        z-index: 100;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
    }
    </style>
    <div class="title">🎬 YouTube Comments Sentiment Analysis</div>
    """,
    unsafe_allow_html=True
)

# Add some spacing to prevent content from being hidden under the fixed title
st.write("\n\n")
# User Input for YouTube Video ID
st.markdown("### 🔎 Enter YouTube Video ID")
video_id = st.text_input("Paste the Video ID below and run the pipeline:", "")


# Run ETL Pipeline
if st.button("🚀 Run ETL Pipeline"):
    if not video_id:
        st.warning("⚠️ Please enter a valid Video ID!")
    else:
        # Trigger the Airflow DAG
        response = requests.post(AIRFLOW_TRIGGER_URL, json={"conf": {"video_id": video_id}}, auth=("airflow", "airflow"))

        if response.status_code == 200:
            dag_run_id = response.json()["dag_run_id"]
            st.success(f"✅ DAG Triggered Successfully! Run ID: `{dag_run_id}`")

            # Polling for DAG completion
            with st.spinner("⏳ Waiting for DAG execution to complete..."):
                while True:
                    status_response = requests.get(AIRFLOW_DAG_STATUS_URL + dag_run_id, auth=("airflow", "airflow"))
                    dag_status = status_response.json().get("state", "")

                    if dag_status in ["success", "failed"]:
                        break
                    time.sleep(5)  # Wait before checking status again
            
            # Check DAG execution status
            if dag_status == "success":
                st.success("🎉 DAG Execution Completed Successfully!")

                # Fetch Results from PostgreSQL
                conn = psycopg2.connect(dbname="YouTubeComments", user="airflow", password="airflow", host="localhost", port="5433")

                # Fetch Video Metadata
                st.markdown("### 🎥 YouTube Video Metadata")
                metadata_query = f"""
                SELECT title AS video_title, channel_title, published_at AS video_posted_date, comment_count, view_count, like_count  
                FROM VideoMetadata WHERE video_id = '{video_id}';
                """
                metadata_df = pd.read_sql_query(metadata_query, conn)
                # # st.dataframe(metadata_df, width=800)
                st.dataframe(metadata_df.style.hide(axis="index"), width=800)
                # # Apply bold styling to column headers and hide index
                # styled_df = metadata_df.style.set_table_styles(
                #     [{"selector": "th", "props": [("font-weight", "bold")]}]
                # ).hide(axis="index")

                # # Display the dataframe in Streamlit
                # st.dataframe(styled_df, width=800)
                # Fetch Comments
                df = pd.read_sql_query("SELECT * FROM Comments", conn)
                # Display Comments Table with Sentiment
                # st.markdown("### 💬 Comments")
                # st.dataframe(df[["author", "published_at", "like_count", "text"]], height=400)
                # Perform Sentiment Analysis
                st.markdown("### 🤖 Sentiment Analysis on Comments")
                
                if client:
                    # Use Hugging Face API for sentiment analysis
                    sentiments = []
                    
                    for text in df["text"]:
                        try:
                            result = client.text_classification(text)
                            # Handle different model output formats
                            if isinstance(result, list) and len(result) > 0:
                                label = result[0].get("label", "neutral")
                                # Convert 5-star rating to sentiment
                                if "1 star" in label or "2 star" in label:
                                    sentiment = "negative"
                                elif "3 star" in label:
                                    sentiment = "neutral"
                                else:
                                    sentiment = "positive"
                                sentiments.append(sentiment)
                            else:
                                sentiments.append("neutral")
                        except Exception as e:
                            # Fallback to simple keyword-based sentiment analysis
                            text_lower = text.lower()
                            positive_words = ['good', 'great', 'awesome', 'excellent', 'amazing', 'love', 'like', 'best', 'perfect']
                            negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'dislike', 'horrible', 'terrible']
                            
                            positive_count = sum(1 for word in positive_words if word in text_lower)
                            negative_count = sum(1 for word in negative_words if word in text_lower)
                            
                            if positive_count > negative_count:
                                sentiment = "positive"
                            elif negative_count > positive_count:
                                sentiment = "negative"
                            else:
                                sentiment = "neutral"
                            
                            sentiments.append(sentiment)
                    
                    df["sentiment"] = sentiments
                else:
                    # Mock sentiment analysis for demonstration
                    mock_sentiments = ["positive", "negative", "neutral"]
                    df["sentiment"] = [random.choice(mock_sentiments) for _ in range(len(df))]
                    st.info("ℹ️ Using mock sentiment analysis. Get a Hugging Face token for real analysis.")

                # Layout: Display Video & Sentiment Distribution Side-by-Side
                col1, col2 = st.columns(2)

                # Display YouTube Video
                with col1:
                    st.subheader("📺 Video Preview")
                    st.video(f"https://www.youtube.com/embed/{video_id}")

                # Sentiment Distribution Pie Chart
                with col2:
                    st.subheader("📊 Sentiment Distribution")
                    sentiment_counts = df["sentiment"].value_counts()
                    fig, ax = plt.subplots()
                    ax.pie(sentiment_counts, labels=sentiment_counts.index, autopct='%1.1f%%', startangle=90)
                    ax.axis("equal")
                    st.pyplot(fig)

                # # Display Comments Table with Sentiment
                # st.markdown("### 💬 Comments with Sentiment")
                # st.dataframe(df[["author", "published_at", "like_count", "text", "sentiment"]], height=400)

                conn.close()
            else:
                st.error("❌ DAG Execution Failed!")
        else:
            st.error("❌ Failed to trigger DAG. Check Airflow API and authentication.")