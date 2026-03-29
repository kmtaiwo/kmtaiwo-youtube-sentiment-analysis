# YouTube Comment Sentiment Analyser

Personal project extracted from the [SuperDataScience community course](https://github.com/SuperDataScience-Community-Projects/SDS-CP020-sentiment-analysis-using-youtube). This repository contains only the author’s notebooks, Airflow DAGs, and Streamlit app—not other contributors’ work from the community fork.

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
   git clone https://github.com/kmtaiwo/youtube-comment-sentiment-analyser.git
   cd youtube-comment-sentiment-analyser
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

Your **fork** of `SDS-CP020-sentiment-analysis-using-youtube` can stay as-is on GitHub. This repo is a **separate** repository (`youtube-comment-sentiment-analyser`) with only your files, so you do not need to delete or modify the community fork.

### First-time push to `kmtaiwo/youtube-comment-sentiment-analyser`

If the GitHub repo is empty:

```bash
cd youtube-comment-sentiment-analyser
git init
git add .
git commit -m "Initial import: notebooks, Airflow DAGs, Streamlit app"
git branch -M main
git remote add origin https://github.com/kmtaiwo/youtube-comment-sentiment-analyser.git
git push -u origin main
```

## License

Community course materials remain subject to the original SDS project terms; code authored here is provided as-is for learning and portfolio use.
