from pymongo import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd

MONGO_URI = "mongodb+srv://rachidmkd16:gVvZdKv4L8EArNjC@news-database.kjitsql.mongodb.net/?retryWrites=true&w=majority&appName=news-database"
DB_NAME = 'news_database'
VECTOR_COUNTS_COLLECTION = 'vector_counts'
ARTICLE_COUNTS_COLLECTION = 'article_counts'
DAILY_ARTICLE_COUNTS_COLLECTION = 'daily_article_counts'
QA_COLLECTION = 'tracking'

client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client[DB_NAME]


def get_vector_counts():
    cursor = db[VECTOR_COUNTS_COLLECTION].find({})
    df = pd.DataFrame(list(cursor))
    df = df.drop('_id', axis=1)
    return df

def get_article_total_counts():
    cursor = db[ARTICLE_COUNTS_COLLECTION].find({})
    df = pd.DataFrame(list(cursor))
    df = df.drop('_id', axis=1)
    return df

def get_daily_article_counts():
    cursor = db[DAILY_ARTICLE_COUNTS_COLLECTION].find({})
    df = pd.DataFrame(list(cursor))
    df = df.drop('_id', axis=1)
    return df


def get_qa():
    cursor = db[QA_COLLECTION].find({})
    df = pd.DataFrame(list(cursor))
    df = df.drop('_id', axis=1)
    df = df[['question', 'answer', 'upvote', 'downvote', 'flag', 'timestamp']]
    return df