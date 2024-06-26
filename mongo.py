<<<<<<< HEAD
from pymongo import MongoClient # load the MongoClient class from the pymongo module
from pymongo.server_api import ServerApi # load the ServerApi class from the pymongo.server_api module
import pandas as pd # load the pandas module and rename it as pd
#==================================================================================================
# define the MongoDB URI
MONGO_URI = "mongodb+srv://rachidmkd16:gVvZdKv4L8EArNjC@news-database.kjitsql.mongodb.net/?retryWrites=true&w=majority&appName=news-database"
DB_NAME = 'news_database' # define the database name
VECTOR_COUNTS_COLLECTION = 'vector_counts' # define the collection name
ARTICLE_COUNTS_COLLECTION = 'article_counts' # define the collection name
DAILY_ARTICLE_COUNTS_COLLECTION = 'daily_article_counts' # define the collection name
QA_COLLECTION = 'tracking' # define the collection name
#==================================================================================================
client = MongoClient(MONGO_URI, server_api=ServerApi('1')) # create a MongoClient object
db = client[DB_NAME] # create a database object
#==================================================================================================
def get_vector_counts(): # define a function to get the vector counts
    cursor = db[VECTOR_COUNTS_COLLECTION].find({}) # get all the documents from the collection
    df = pd.DataFrame(list(cursor)) # convert the cursor to a DataFrame
    df = df.drop('_id', axis=1) # drop the _id column
    return df # return the DataFrame
#==================================================================================================
def get_article_total_counts():
    cursor = db[ARTICLE_COUNTS_COLLECTION].find({})
    df = pd.DataFrame(list(cursor))
    df = df.drop('_id', axis=1)
    return df
#==================================================================================================
def get_daily_article_counts():
    cursor = db[DAILY_ARTICLE_COUNTS_COLLECTION].find({})
    df = pd.DataFrame(list(cursor))
    df = df.drop('_id', axis=1)
    return df
#==================================================================================================
def get_qa():
    cursor = db[QA_COLLECTION].find({})
    df = pd.DataFrame(list(cursor))
    df = df.drop('_id', axis=1)
    df = df[['question', 'answer', 'upvote', 'downvote', 'flag', 'timestamp']]
    return df

=======
from pymongo import MongoClient # load the MongoClient class from the pymongo module
from pymongo.server_api import ServerApi # load the ServerApi class from the pymongo.server_api module
import pandas as pd # load the pandas module and rename it as pd
#==================================================================================================
# define the MongoDB URI
MONGO_URI = "mongodb+srv://rachidmkd16:gVvZdKv4L8EArNjC@news-database.kjitsql.mongodb.net/?retryWrites=true&w=majority&appName=news-database"
DB_NAME = 'news_database' # define the database name
VECTOR_COUNTS_COLLECTION = 'vector_counts' # define the collection name
ARTICLE_COUNTS_COLLECTION = 'article_counts' # define the collection name
DAILY_ARTICLE_COUNTS_COLLECTION = 'daily_article_counts' # define the collection name
QA_COLLECTION = 'tracking' # define the collection name
#==================================================================================================
client = MongoClient(MONGO_URI, server_api=ServerApi('1')) # create a MongoClient object
db = client[DB_NAME] # create a database object
#==================================================================================================
def get_vector_counts(): # define a function to get the vector counts
    cursor = db[VECTOR_COUNTS_COLLECTION].find({}) # get all the documents from the collection
    df = pd.DataFrame(list(cursor)) # convert the cursor to a DataFrame
    df = df.drop('_id', axis=1) # drop the _id column
    return df # return the DataFrame
#==================================================================================================
def get_article_total_counts():
    cursor = db[ARTICLE_COUNTS_COLLECTION].find({})
    df = pd.DataFrame(list(cursor))
    df = df.drop('_id', axis=1)
    return df
#==================================================================================================
def get_daily_article_counts():
    cursor = db[DAILY_ARTICLE_COUNTS_COLLECTION].find({})
    df = pd.DataFrame(list(cursor))
    df = df.drop('_id', axis=1)
    return df
#==================================================================================================
def get_qa():
    cursor = db[QA_COLLECTION].find({})
    df = pd.DataFrame(list(cursor))
    df = df.drop('_id', axis=1)
    df = df[['question', 'answer', 'upvote', 'downvote', 'flag', 'timestamp']]
    return df

>>>>>>> 0ec6562bb0b91b75d665cba45af649bbc775c020
# ==============================================================================================================================================