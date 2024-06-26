# Description: This file contains the code to preprocess the data and generate embeddings for the text data.
from transformers import BertTokenizer, BertModel # Import the BERT Tokenizer and Model
import torch # Import the PyTorch library
# ==============================================================================================================================================
# Function to compute the cosine similarity
class TextEmbedder: # Create a class to embed the text
    def __init__(self): 
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased') # Load BERT Tokenizer
        self.model = BertModel.from_pretrained('bert-base-uncased') # Load BERT Model
    # Function to compute the cosine similarity
    def _mean_pooling(self, model_output, attention_mask):  
        '''
        This function computes the mean pooling of the embeddings

        Parameters:
        ----------
        model_output: model output
        attention_mask: attention mask

        Returns:
        -------
        mean embeddings
        '''
        token_embeddings = model_output.last_hidden_state # Get the token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float() # Expand the attention mask
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1) # Sum the embeddings
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9) # Clamp the sum of the mask
        return sum_embeddings / sum_mask # Return the mean embeddings
    # Function to embed the text
    def embed_text(self, examples): 
        # Tokenize the input text
        inputs = self.tokenizer(
            examples["content"], padding=True, truncation=True, return_tensors="pt"
        )
        with torch.no_grad(): # Disable gradient calculation for efficiency
            model_output = self.model(**inputs) # Get the model output
        pooled_embeds = self._mean_pooling(model_output, inputs["attention_mask"]) # Get the pooled embeddings
        return {"embedding": pooled_embeds.cpu().numpy()} # Return the embeddings
    
    def generate_embeddings(self, dataset): # Function to generate the embeddings
        return dataset.map(self.embed_text, batched=True, batch_size=128) # Map the embed_text function to the dataset
# ==============================================================================================================================================
    # Function to embed the query
    def embed_query(self, query_text):
        query_inputs = self.tokenizer(
            query_text,
            padding=True,
            truncation=True,
            return_tensors="pt"
        )

        with torch.no_grad():
            query_model_output = self.model(**query_inputs)

        query_embedding = self._mean_pooling(query_model_output, query_inputs["attention_mask"])

        return query_embedding

# ==============================================================================================================================================
# ==============================================================================================================================================