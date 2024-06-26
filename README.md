# News and Finance Article Processing System

## Overview

The News and Finance Article Processing System is designed to retrieve, process, and analyze news and financial articles using modern APIs and machine learning techniques. The system fetches articles from specified news and finance APIs, preprocesses the data, converts them into embeddings using a text embedding model, and stores the embeddings in a Qdrant database for further analysis and retrieval. Additionally, it tracks the number of articles and vectors, storing this information in a MongoDB database.

## Features

- **Data Collection:** Fetches articles from multiple news and finance APIs (e.g., NewsAPI, GuardianAPI, GNews).
- **Data Preprocessing:** Cleans and prepares the raw data for processing.
- **Text Embedding:** Converts text into vector embeddings using a text embedding model (e.g., BERT).
- **Data Storage:** Stores the embeddings in a Qdrant database for efficient retrieval.
- **Article and Vector Count Tracking:** Tracks and stores the number of articles and vectors in a MongoDB database.
- **Streamlit Dashboard:** Provides an interactive dashboard to visualize the number of articles and vectors over time.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.8+
- Access to the APIs (NewsAPI, GuardianAPI, AlphaVantage API, GNews API)
- MongoDB Atlas account
- Qdrant account
- Streamlit

# Project Structure

- collector.py: Script for collecting and processing news and financial articles.
- dashboard.py: Streamlit dashboard for visualizing the collected data.
- requirements.txt: List of required Python packages.
