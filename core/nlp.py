import os
from xml.parsers.expat import model
import certifi
from sentence_transformers import SentenceTransformer

os.environ['SSL_CERT_FILE'] = certifi.where()



sbert_model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text: str):
    return sbert_model.encode(text).tolist()  # convert numpy → list