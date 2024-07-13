import re 
from semantic_text_splitter import TiktokenTextSplitter 
from datasets import Dataset 
from transformers import BertTokenizer, BertModel 
from sklearn.metrics.pairwise import cosine_similarity
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification 

model__deberta = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli" # DeBERTa Model
tokenizer_deberta = AutoTokenizer.from_pretrained(model__deberta) # DeBERTa Tokenizer 
model_deberta = AutoModelForSequenceClassification.from_pretrained(model__deberta) # loading DeBERTa Model

# Function to remove HTML tags from the text
def remove_tags(input_text):
        '''Remove HTML tags from a string
        
        Parameters:
        -----------
        input_text : str
            The input string containing HTML tags
            
        '''
        clean_text = re.sub('<.*?>', '', input_text) 
        timing_pattern = r'\b\d{1,2}\.\d{2}[apmAPM]+\s+[GMTgmt]+\b' 
        clean_text = re.sub(timing_pattern, '', clean_text) 
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = clean_text.replace('\n', ' ')
        pattern = r'© \d+ BBC\. The BBC is not responsible for the content of external sites\. Read about our approach to external linking\.'
        clean_text = re.sub(pattern, '', clean_text)
        return clean_text
# ==============================================================================================================================================
# Function to process the articles
def process_articles(collected_articles):
        chunked_articles = []
        chunked_titles = []
        chunked_pubdate=[]
        for article in collected_articles:  
            max_tokens = 512 
            splitter = TiktokenTextSplitter("gpt-3.5-turbo", trim_chunks=False)
            chunks = splitter.chunks(article['content'], max_tokens)
            for chunk in chunks:
                chunked_articles.append(chunk)
                chunked_titles.append(article['title'])
                chunked_pubdate.append(article['publishdate'])
        data_dict = {
            "title": chunked_titles,
            "content": chunked_articles,
            "publishdate": chunked_pubdate,
        }
        dataset = Dataset.from_dict(data_dict)
        return dataset

# ==============================================================================================================================================

def Entailment_score(question , response):
    inputs = tokenizer_deberta(question, response, return_tensors="pt", padding=True, truncation=True)
    logits = model_deberta(**inputs).logits
    entailment_score = F.softmax(logits, dim=1)[0][0].item()
    return entailment_score

def compute_entailment_score(row):
    question = row['question']
    response = row['answer']
    row['Entailment'] = Entailment_score(question, response)
    return row

# ==============================================================================================================================================
# Function to compute the cosine similarity
def bert_cosine_similarity(question, answer):
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')  # Load BERT Tokenizer
    model = BertModel.from_pretrained('bert-base-uncased') # Load BERT Model
    input_dict = tokenizer(question, answer, return_tensors='pt', padding=True, truncation=True) # Tokenize the input
    outputs = model(**input_dict) 
    embeddings = outputs.last_hidden_state
    query_embedding = embeddings[0][0] 
    answer_embedding = embeddings[0][1] 
    cosine_score = cosine_similarity(query_embedding.detach().numpy().reshape(1, -1), answer_embedding.detach().numpy().reshape(1, -1)) # Compute the cosine similarity
    return cosine_score[0][0] 
# Function to compute the cosine similarity
def compute_bert_cosine_similarity(row): 
    question = row['question']
    response = row['answer']
    row['cosine_similarity'] = bert_cosine_similarity(question, response)
    return row
