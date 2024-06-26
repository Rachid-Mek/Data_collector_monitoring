# Description: This file contains the class QdrantU which is used to interact with the Qdrant database. It contains methods to upload documents to the database, get the number of vectors in the database, search for similar documents, count the number of vectors by source and retrieve vectors by source.
import uuid # Import the uuid module to generate unique identifiers
from qdrant_client.http import models # Import the models module from the qdrant_client.http module
from qdrant_client import QdrantClient # Import the QdrantClient class from the qdrant_client module
import logging # Import the logging module
# ==============================================================================================================================================
# Setup logging
logging.basicConfig(level=logging.INFO)

class QdrantU: # Create a class QdrantU
    def __init__(self, collection_name,timeout=7200): # Define the constructor
        self.client = QdrantClient( # Create a QdrantClient object
            url="https://c60e574c-c519-4fbb-be80-1710d3b73053.europe-west3-0.gcp.cloud.qdrant.io",
            api_key="njaSPeFbhkN1jPqOXUMdimkDkOasd2FAbENpGwlL2NXQG2LsxAHY-g",
            timeout=timeout
        )
        self.collection_name = collection_name

    def _upload_documents_to_Qdrant(self, data, source): # Define a method to upload documents to Qdrant
        points = [] # Create an empty list to store the points
        for title, content, publishdate, embedding in zip(data["title"], data["content"], data["publishdate"], data["embedding"]):
            new_id = str(uuid.uuid4())  # Generate a new UUID for each document
            point = models.PointStruct(
                id=new_id,
                vector=embedding,
                payload={
                    "title": title,
                    "content": content,
                    "publishdate": publishdate,
                    "source" : source
                }
            )
            points.append(point)

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        logging.info(f"Uploaded {len(data['embedding'])} documents to the Qdrant database")

    # Function to upload the data to Qdrant
    def upload_to_Qdrant(self, data, batch_size=35, source=''):
        for i in range(0, len(data), batch_size):   
            batch = data[i:i + batch_size]  
            self._upload_documents_to_Qdrant(batch , source)
            logging.info(f"Uploaded {i + len(batch)} documents")

    # Function to get the number of vectors in the database
    def get_number_of_vectors(self):
        # try:
            collection_info = self.client.get_collection(self.collection_name)
            num_vectors = collection_info.points_count
            return num_vectors
        # except Exception as e:
        #     logging.error("Failed to get number of vectors:", exc_info=True)
        #     return None
    
    # Function to close the connection
    def close_connection(self):
        self.client.close()
# ==============================================================================================================================================
    # Function to search for similar documents
    def search(self, query, text_embedder, limit):
        query_vector = text_embedder.embed_query(query_text=query)
        query_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector[0].tolist(),  # Convert tensor to list
            limit=limit,
            with_payload=True
        )
        return query_result
# ==============================================================================================================================================
    # Function to count the number of vectors by source
    def count_vectors_by_source(self, source):
        count = self.client.count(
            collection_name=self.collection_name,
            count_filter=models.Filter(
                must=[
                    models.FieldCondition(key="source", match=models.MatchValue(value=source)),
                ]
            ),
            exact=True,
        )
        return count.count
# ==============================================================================================================================================
    # Function to retrieve vectors by source
    def retrieve_vectors_by_source(self, source):
        vectors = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(key="source", match=models.MatchValue(value=source)),
                ]
            ),
            limit=300,
            with_payload=True,
        )
        return vectors
    
# ==============================================================================================================================================
# ==============================================================================================================================================