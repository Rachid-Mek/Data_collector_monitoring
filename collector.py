from time import sleep # To avoid hitting the rate limit of the APIs
from News_collector import News_collector # import the News_collector class
from Processing import TextEmbedder  # import the TextEmbedder class
from QdrantU import QdrantU # import the QdrantU class
from Finance_business import Finance_business # import the Finance_business class
from pymongo import MongoClient # import pymongo to connect to the MongoDB database
from pymongo.server_api import ServerApi # import the ServerApi to connect to the MongoDB database
from datetime import datetime # import datetime to get the current date
from qdrant_client.http import models # import the models from the qdrant_client.http
import logging # import logging to log the information

# Setup logging
logging.basicConfig(level=logging.INFO)

# API Keys for the different APIs
NEWSAPI_KEY_1 = 'fbca2746989b4ed69c12fc943fd33650' # First News API Key for fetching news articles
NEWSAPI_KEY_2 = '3d40d72f4efd4810901e62b9253c8731' # Second News API Key for fetching news articles
GUARDIANAPI = 'd69e575e-91d0-45c1-97f4-ac0fe69f9899' # Guardian API Key for fetching news articles
ALPHA_API = 'SPIKC6LBBQ3VUG8C' # Alpha Vantage API Key for fetching stock data
GNEWS_API_KEY = "90864491d78ef53542020d240753e2f0" # GNews API Key for fetching news articles
# MongoDB URI and Database name to connect to the MongoDB database
MONGO_URI = "mongodb+srv://rachidmkd16:gVvZdKv4L8EArNjC@news-database.kjitsql.mongodb.net/?retryWrites=true&w=majority&appName=news-database"
DB_NAME = 'news_database' # Database name to connect to the MongoDB database
VECTOR_COUNTS_COLLECTION = 'vector_counts' # Collection name to store the vector counts
ARTICLE_COUNTS_COLLECTION = 'article_counts' # Collection name to store the article counts
DAILY_ARTICLE_COUNTS_COLLECTION = 'daily_article_counts' # Collection name to store the daily article counts

client = MongoClient(MONGO_URI, server_api=ServerApi('1')) # Connect to the MongoDB database using the MongoClient
db = client[DB_NAME] # Connect to the database using the database name
# the function to save the total number of articles
def save_vector_count(date, count):  # Save the total number of articles
    # Save the total number of articles in the database
    db[VECTOR_COUNTS_COLLECTION].update_one( 
        {"date": date}, 
        {"$set": {"vector_count": count}},
        upsert=True
    )
# the function to save the total number of articles for a given source
def save_total_article_count(date, source, count):
    '''
    Save the total number of articles for a given source.
    '''
    db[ARTICLE_COUNTS_COLLECTION].update_one(
        {"date": date, "source": source},
        {"$set": {"nb_article": count}},
        upsert=True
    )
# the function to save the daily count of articles per source
def save_daily_article_count(date, source, count):
    '''
    Save the daily count of articles per source.
    '''
    db[DAILY_ARTICLE_COUNTS_COLLECTION].update_one(
        {"date": date, "source": source},
        {"$set": {"count": count}},
        upsert=True
    )
# the function to count the articles by source
def count_articles_by_source(client, collection_name, source_name):
    try: # Try to count the articles by source
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
    except Exception as e: # Handle the exception
        logging.error(f"Error counting articles by source: {e}")
        return 0
    
news_collector = News_collector(guardian_api_key=GUARDIANAPI, newsapi_key=NEWSAPI_KEY_1) # Create an instance of the News_collector class
finance_business = Finance_business(guardian_api_key=GUARDIANAPI, alphavantage_api_key=ALPHA_API, newsapi_key=NEWSAPI_KEY_2, gnews_api_key=GNEWS_API_KEY)
current_date = datetime.now().strftime("%Y-%m-%d") # Get the current date in the format YYYY-MM-DD
# Fetch news articles from different sources
sources = {
    'Guardian': news_collector.fetch_guardian_news(), # Fetch news articles from the Guardian
    'BBC': news_collector.fetch_bbc_news(), # Fetch news articles from the BBC
    'Al Jazeera': news_collector.fetch_al_jazeera_english(), # Fetch news articles from Al Jazeera
    'ABC': news_collector.fetch_abc_news(), # Fetch news articles from ABC News
    'GNews': finance_business.fetch_gnews_articles(), # Fetch news articles from GNews
    'CNN': news_collector.get_cnn_news(), # Fetch news articles from CNN
    'Fortune': finance_business.fetch_fortune_news(), # Fetch news articles from Fortune
    'ABC AU': news_collector.fetch_abc_news_au_articles(), # Fetch news articles from ABC News Australia
    'Fox News': news_collector.fetch_fox_news(), # Fetch news articles from Fox News
    'Washington Post': news_collector.fetch_washington_post(), # Fetch news articles from the Washington Post
    'Forbes': finance_business.fetch_forbes_news(), # Fetch news articles from Forbes
    'CNBC': finance_business.fetch_cnbc_news(), # Fetch news articles from CNBC
    'New York Post': news_collector.fetch_new_york_post(), # Fetch news articles from the New York Post
    'Wired': finance_business.fetch_wired_news(), # Fetch news articles from Wired
    'Ambcrypto': finance_business.fetch_ambcrypto_news(), # Fetch news articles from Ambcrypto
    'USA Today': news_collector.fetch_usa_today(), # Fetch news articles from USA Today
    'NPR': news_collector.fetch_npr_news(), # Fetch news articles from NPR
    'AP News': news_collector.fetch_ap_news(), # Fetch news articles from AP News
    'Coindesk': finance_business.fetch_coindesk_news(), # Fetch news articles from Coindesk
    'Bitcoinist': finance_business.fetch_bitcoinist_news(), # Fetch news articles from Bitcoinist
    'Investing': finance_business.fetch_investing_news(), # Fetch news articles from Investing.com
    'Coinjournal': finance_business.fetch_coinjournal_news(), # Fetch news articles from Coinjournal
    'business insider': finance_business.fetch_businessinsider_news(), # Fetch news articles from Business Insider
    'readwrite': finance_business.fetch_readwrite_news(), # Fetch news articles from ReadWrite
    'sky sports': news_collector.fetch_sky_news(), # Fetch news articles from Sky News
}


if __name__ == "__main__":
    total_articles = 0 # Initialize the total number of articles to 0
    embedding_model = TextEmbedder() # Create an instance of the TextEmbedder class
    uploader = QdrantU(collection_name='News_Articles_Source') # Create an instance of the QdrantU class
    number_vectors = uploader.get_number_of_vectors() # Get the number of vectors in the collection
    print("Number of vectors in the collection:", number_vectors) # Print the number of vectors in the collection
    for source, articles in sources.items():
        print(f"Processing articles from {source}...") # Print the source of the articles
        embeddings = embedding_model.generate_embeddings(articles) # Generate embeddings for the articles
        print(f"Number of articles from {source}:", len(embeddings)) # Print the number of articles from the source
        total_articles += len(embeddings) # Update the total number of articles
        save_daily_article_count(current_date, source, len(embeddings)) # Save the daily count of articles per source

        uploader.upload_to_Qdrant(data=embeddings, source=source) # Upload the embeddings to Qdrant
        # Count articles by source and save total article count
        article_count = count_articles_by_source(uploader.client, 'News_Articles_Source', source) # Count the articles by source
        print(f"Number of articles from {source}:", article_count) # Print the number of articles from the source
        save_total_article_count(current_date, source, article_count) # Save the total number of articles for the source
        
        sleep(2) # Sleep for 2 seconds to avoid hitting the rate limit of the APIs
    
    # Save the total number of articles
    total_articles += number_vectors # Add the number of vectors to the total number of articles
    save_vector_count(current_date, total_articles) # Save the total number of articles
    print("Total number of articles:", total_articles) # Print the total number of articles
    print('----------------------------------------Done----------------------------------------') # Print Done
    uploader.close_connection() # Close the connection to Qdrant

#==============================================================================================================================================
