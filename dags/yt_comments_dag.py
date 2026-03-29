# #dag - directed acyclic graph
# #dag tasks are:
# (1) fetch YouTube comments as data (extract)
# (2) clean data (transform)
# (3) create and store data in table on postgres (load)
# #operators : Python Operator and PostgresOperator
# #hooks - allows connection to postgres
# #dependencies
from airflow import DAG
from airflow.decorators import task
from airflow.utils.dates import days_ago
import string
import requests
import json
import random
import re
import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd
import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()
#
print("os.getenv(ytb_api):1",os.getenv("ytb_api"))
default_args={
    'owner':'airflow',
    'start_date':days_ago(1)
}

## DAG
with DAG(dag_id='youtube_comments_etl_pipeline',
         default_args=default_args,
         schedule_interval='@daily',
         catchup=False) as dags:
    
    @task()
    def extract_video_metadata(**context):
        """Extract video metadata from YouTube API."""
        # Get video_id from DAG configuration or use default
        dag_run = context['dag_run']
        video_id = dag_run.conf.get('video_id', 'SIm2W9TtzR0')  # Default fallback
        
        input_params = { "video_id" : video_id, 
                "api_service_name" : "youtube",
                "api_version" : "v3",
                "DEVELOPER_KEY": os.getenv("ytb_api")
                }
        print("Extracting metadata for video_id:", video_id)
        youtube = googleapiclient.discovery.build(
            input_params["api_service_name"], input_params["api_version"], developerKey=input_params["DEVELOPER_KEY"])
        
        # Get video details
        request = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        )
        response = request.execute()
        
        if response['items']:
            video_info = response['items'][0]
            snippet = video_info['snippet']
            statistics = video_info.get('statistics', {})
            
            metadata = {
                'video_id': video_id,
                'title': snippet.get('title', ''),
                'channel_title': snippet.get('channelTitle', ''),
                'published_at': snippet.get('publishedAt', ''),
                'comment_count': statistics.get('commentCount', 0),
                'view_count': statistics.get('viewCount', 0),
                'like_count': statistics.get('likeCount', 0)
            }
            return metadata
        else:
            return None
        
    @task()
    def extract_youtube_data(**context):
        """Extract youtube comments from youtube API."""
        # Get video_id from DAG configuration or use default
        dag_run = context['dag_run']
        video_id = dag_run.conf.get('video_id', 'SIm2W9TtzR0')  # Default fallback
        
        input_params = { "video_id" : video_id, 
                "api_service_name" : "youtube",
                "api_version" : "v3",
                "DEVELOPER_KEY": os.getenv("ytb_api")
                }
        print("os.getenv(ytb_api):2",os.getenv("ytb_api"))
        print("Using video_id:", video_id)
        youtube = googleapiclient.discovery.build(
            input_params["api_service_name"], input_params["api_version"], developerKey=input_params["DEVELOPER_KEY"])
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=input_params["video_id"],
            maxResults=23
        )
        response = request.execute()
        return response       
        
    @task()
    def transform_youtube_data(youtube_data):
        """Transform the extracted youtube data."""
        # def contains_url(text):
        #     url_pattern = re.compile(r'https?://\S+|www\.\S+')
        #     return bool(url_pattern.search(text))
        def remove_URL(text):
            url = re.compile(r'https?://\S+|www\.\S+')
            return url.sub(r'',text)
        def remove_emoji(text):
            emoji_pattern = re.compile("["
                                u"\U0001F600-\U0001F64F"  # emoticons
                                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                u"\U00002702-\U000027B0"
                                u"\U000024C2-\U0001F251"
                                "]+", flags=re.UNICODE)
            return emoji_pattern.sub(r'', text)
        def remove_punct(text):
            table=str.maketrans('','',string.punctuation)
            return text.translate(table)        
        comments = []

        for item in youtube_data['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            comments.append([
                comment['authorDisplayName'],
                comment['publishedAt'],
                comment['updatedAt'],
                comment['likeCount'],
                comment['textOriginal']
            ])
        #Check if the text data has URL: Source: ChatGPT
        transformed_data = pd.DataFrame(comments, columns=['author', 'published_at', 'updated_at', 'like_count', 'text'])
        print("transformed_data.head() before cleaning:",transformed_data.head())
        transformed_data['text'] = transformed_data['text'].apply(lambda x : remove_URL(x))
        transformed_data['text'] = transformed_data['text'].apply(lambda x : remove_emoji(x))
        transformed_data['text'] = transformed_data['text'].apply(lambda x : remove_punct(x))
        # transformed_data['like_count'] = transformed_data['like_count'].astype(int)
        print("transformed_data.head():",transformed_data.head())
        return transformed_data
    
    @task()
    def load_youtube_data(video_metadata, transformed_data):
        """Load transformed data into PostgreSQL."""
        # Use direct connection instead of undefined youtube_connection
        conn = psycopg2.connect(
            dbname="YouTubeComments", 
            user="airflow", 
            password="airflow", 
            host="youtube-postgres", 
            port="5432"
        )
        cursor = conn.cursor()
        
        # Create VideoMetadata table
        cursor.execute("""
            DROP TABLE IF EXISTS VideoMetadata CASCADE;
            CREATE TABLE IF NOT EXISTS VideoMetadata (
                video_id TEXT PRIMARY KEY,
                title TEXT,
                channel_title TEXT,
                published_at TIMESTAMP,
                comment_count INT,
                view_count INT,
                like_count INT
            );
        """)
        
        # Insert video metadata
        if video_metadata:
            metadata_query = """
            INSERT INTO VideoMetadata (video_id, title, channel_title, published_at, comment_count, view_count, like_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(metadata_query, (
                video_metadata['video_id'],
                video_metadata['title'],
                video_metadata['channel_title'],
                video_metadata['published_at'],
                video_metadata['comment_count'],
                video_metadata['view_count'],
                video_metadata['like_count']
            ))
        
        # Create Comments table
        cursor.execute("""
            DROP TABLE IF EXISTS Comments CASCADE;
            CREATE TABLE IF NOT EXISTS Comments (
                author TEXT,
                published_at TIMESTAMP,
                updated_at TIMESTAMP,
                like_count INT,
                text TEXT
            );
        """)
        
        # Insert transformed data into the Comments table
        insert_query = """
        INSERT INTO Comments (author, published_at, updated_at, like_count, text)
        VALUES (%s, %s, %s, %s, %s)
        """
        # Convert DataFrame rows to tuples for insertion
        records = [(row.author, row.published_at, row.updated_at, int(row.like_count), 
                    row.text) for row in transformed_data.itertuples(index=False) ]
        
        for record in records:
            cursor.execute(insert_query, record)                
        conn.commit()
        
        # Return both tables data
        comments_data = pd.read_sql_query("SELECT * FROM Comments", conn)
        metadata_data = pd.read_sql_query("SELECT * FROM VideoMetadata", conn)
        cursor.close()
        conn.close()
        return {"comments": comments_data, "metadata": metadata_data}
        
    ## DAG Worflow- ETL Pipeline
    video_metadata = extract_video_metadata()
    comments_data = extract_youtube_data()
    transformed_data = transform_youtube_data(comments_data)
    clean_data = load_youtube_data(video_metadata, transformed_data)