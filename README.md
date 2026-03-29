# YouTube Comment Sentiment Analyser

#### Introduction: ###
This project analyses sentiment in YouTube comments to understand audience reactions and engagement. It uses a machine learning pipeline (including Hugging Face transformers in the Streamlit app), an Airflow ETL flow for YouTube API data, and exploratory notebooks.


#### Problem Definition: ###
Content creators, marketers, and analysts often need to understand how audiences feel about specific videos or channels. Manually reading thousands of comments is not practical. This project automates the full workflow: extract comments, clean the text, classify sentiment, and visualise the results.

Personal project extracted from the [SuperDataScience community course](https://github.com/SuperDataScience-Community-Projects/SDS-CP020-sentiment-analysis-using-youtube). This repository contains only the author’s notebooks, Airflow DAGs, and Streamlit app—not other contributors’ work from the community fork.


#### Approach:

1. **Data extraction  —**  Used the YouTube Data API v3 to fetch comments and metadata for any public video
2. **Preprocessing —** Cleaned raw comment text (removed URLs, emojis, special characters) and tokenised for model input
3. **Sentiment classification —** Applied a pre-trained Hugging Face transformer model (cardiffnlp/twitter-roberta-base-sentiment-latest) to classify each comment
4. **Visualisation —** Built a Streamlit app where users paste a YouTube URL and see sentiment breakdowns, word clouds, and distribution charts

## What’s in this repo

| Path | Purpose |
|------|--------|
| `notebooks/` | Exploratory work: `kmt3-yt-project.ipynb`, `kmtaiwo_yt_eda.ipynb` |
| `dags/` | Airflow ETL: `youtube_comments_etl_pipeline` (`yt_comments_dag.py`) and manual test DAG `yt_comments_etl_test` (`ytc_test.py`) |
| `app/streamlit_app.py` | Streamlit UI to trigger the DAG and run sentiment analysis |
| `docker-compose.yaml` | Local Apache Airflow stack (aligned with Airflow’s official template) |

## Prerequisites

- Python 3.10+ (3.12 works with the pinned stack below)
- [YouTube Data API v3](https://developers.google.com/youtube/v3) key
- Optional: [Hugging Face](https://huggingface.co/) token for live model inference in the Streamlit app
- Docker Desktop (only if you run Airflow via Compose)

## Setup

1. Clone this repository (your GitHub copy):

   ```bash
   git clone https://github.com/kmtaiwo/kmtaiwo-youtube-comment-sentiment-analyser.git
   cd kmtaiwo-youtube-comment-sentiment-analyser
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Environment variables:

   ```bash
   copy .env.example .env
   ```

   Edit `.env` and set `ytb_api` to your YouTube API key and optionally `TestHFToken` for Hugging Face.

## Run Airflow locally

From the project root (where `docker-compose.yaml` and `dags/` live), follow the usual Airflow Docker instructions: set `AIRFLOW_UID` if needed, then `docker compose up`. Mount expects `./dags` → `/opt/airflow/dags`. The DAG connects to PostgreSQL using the host `youtube-postgres` as in the original Compose stack—ensure that service name matches your `docker-compose.yaml` network.

## Run the Streamlit app

```bash
streamlit run app/streamlit_app.py
```

The app calls the Airflow REST API on `http://localhost:8080` by default; start Airflow first if you use that feature.

## Relationship to the SDS fork

Your **fork** of `SDS-CP020-sentiment-analysis-using-youtube` can stay as-is on GitHub. This repo is a **separate** repository ([kmtaiwo/kmtaiwo-youtube-comment-sentiment-analyser](https://github.com/kmtaiwo/kmtaiwo-youtube-comment-sentiment-analyser)) with only your files, so you do not need to delete or modify the community fork.

### Git remote

If you see `Repository not found`, ensure `origin` matches the repo name on GitHub:

```bash
git remote set-url origin https://github.com/kmtaiwo/kmtaiwo-youtube-comment-sentiment-analyser.git
```

If GitHub already has commits (for example an initial README), merge with: `git pull origin main --allow-unrelated-histories`, resolve any conflicts, then `git push -u origin main`.

## License

Community course materials remain subject to the original SDS project terms; code authored here is provided as-is for learning and portfolio use.
