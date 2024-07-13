from time import sleep
from News_collector import News_collector
from Processing import TextEmbedder
from QdrantU import QdrantU
from Finance_business import Finance_business
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
from qdrant_client.http import models
import logging
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)

NEWSAPI_KEY_1 = os.getenv('NEWSAPI_KEY_1')
NEWSAPI_KEY_2 = os.getenv('NEWSAPI_KEY_2')
GUARDIANAPI = os.getenv('GUARDIANAPI')
ALPHA_API = os.getenv('ALPHA_API')
GNEWS_API_KEY = os.getenv('GNEWS_API_KEY')
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')
VECTOR_COUNTS_COLLECTION = os.getenv('VECTOR_COUNTS_COLLECTION')
ARTICLE_COUNTS_COLLECTION = os.getenv('ARTICLE_COUNTS_COLLECTION')
DAILY_ARTICLE_COUNTS_COLLECTION = os.getenv('DAILY_ARTICLE_COUNTS_COLLECTION')
QA_COLLECTION = os.getenv('QA_COLLECTION')

client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client[DB_NAME]

def save_vector_count(date, count):
    db[VECTOR_COUNTS_COLLECTION].update_one(
        {"date": date},
        {"$set": {"vector_count": count}},
        upsert=True
    )

def save_total_article_count(date, source, count):
    db[ARTICLE_COUNTS_COLLECTION].update_one(
        {"date": date, "source": source},
        {"$set": {"nb_article": count}},
        upsert=True
    )

def save_daily_article_count(date, source, count):
    db[DAILY_ARTICLE_COUNTS_COLLECTION].update_one(
        {"date": date, "source": source},
        {"$set": {"count": count}},
        upsert=True
    )

def count_articles_by_source(client, collection_name, source_name):
    try:
        count_result = client.count(
            collection_name=collection_name,
            count_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="source",
                        match=models.MatchValue(value=source_name),
                    ),
                ]
            )
        )
        return count_result.count
    except Exception as e:
        logging.error(f"Error counting articles by source: {e}")
        return 0

news_collector = News_collector(guardian_api_key=GUARDIANAPI, newsapi_key=NEWSAPI_KEY_1)
finance_business = Finance_business(guardian_api_key=GUARDIANAPI, alphavantage_api_key=ALPHA_API, newsapi_key=NEWSAPI_KEY_2, gnews_api_key=GNEWS_API_KEY)
current_date = datetime.now().strftime("%Y-%m-%d")

sources = {
    'Guardian': news_collector.fetch_guardian_news(),
    'BBC': news_collector.fetch_bbc_news(),
    'Al Jazeera': news_collector.fetch_al_jazeera_english(),
    'ABC': news_collector.fetch_abc_news(),
    'CNN': news_collector.get_cnn_news(),
    'Fortune': finance_business.fetch_fortune_news(),
    'ABC AU': news_collector.fetch_abc_news_au_articles(),
    'Fox News': news_collector.fetch_fox_news(),
    'Washington Post': news_collector.fetch_washington_post(),
    'Forbes': finance_business.fetch_forbes_news(),
    'CNBC': finance_business.fetch_cnbc_news(),
    'New York Post': news_collector.fetch_new_york_post(),
    'Wired': finance_business.fetch_wired_news(),
    'Ambcrypto': finance_business.fetch_ambcrypto_news(),
    'USA Today': news_collector.fetch_usa_today(),
    'NPR': news_collector.fetch_npr_news(),
    'AP News': news_collector.fetch_ap_news(),
    'Coindesk': finance_business.fetch_coindesk_news(),
    'Bitcoinist': finance_business.fetch_bitcoinist_news(),
    'Investing': finance_business.fetch_investing_news(),
    'Coinjournal': finance_business.fetch_coinjournal_news(),
    'business insider': finance_business.fetch_businessinsider_news(),
    'readwrite': finance_business.fetch_readwrite_news(),
    'sky sports': news_collector.fetch_sky_news(),
}

if __name__ == "__main__":
    total_articles = 0
    embedding_model = TextEmbedder()
    uploader = QdrantU(collection_name='News_Articles_Source')
    number_vectors = uploader.get_number_of_vectors()
    print("Number of vectors in the collection:", number_vectors)
    for source, articles in sources.items():
        print(f"Processing articles from {source}...")
        embeddings = embedding_model.generate_embeddings(articles)
        print(f"Number of articles from {source}:", len(embeddings))
        total_articles += len(embeddings)
        save_daily_article_count(current_date, source, len(embeddings))

        uploader.upload_to_Qdrant(data=embeddings, source=source)
        article_count = count_articles_by_source(uploader.client, 'News_Articles_Source', source)
        print(f"Number of articles from {source}:", article_count)
        save_total_article_count(current_date, source, article_count)
        
        sleep(2)
    
    total_articles += number_vectors
    save_vector_count(current_date, total_articles)
    print("Total number of articles:", total_articles)
    print('----------------------------------------Done----------------------------------------')
    uploader.close_connection()