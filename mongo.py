from pymongo import MongoClient 
from pymongo.server_api import ServerApi
import pandas as pd 
import os
import dotenv

dotenv.load_dotenv()

# define the MongoDB URI
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
VECTOR_COUNTS_COLLECTION = os.getenv("VECTOR_COUNTS_COLLECTION")
ARTICLE_COUNTS_COLLECTION = os.getenv("ARTICLE_COUNTS_COLLECTION")
DAILY_ARTICLE_COUNTS_COLLECTION = os.getenv("DAILY_ARTICLE_COUNTS_COLLECTION")
QA_COLLECTION = os.getenv("QA_COLLECTION")

client = MongoClient(MONGO_URI, server_api=ServerApi('1')) # create a MongoClient object
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

# ==============================================================================================================================================