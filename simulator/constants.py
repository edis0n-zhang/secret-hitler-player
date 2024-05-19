import os
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

load_dotenv()
openai_client = OpenAI()

pinecone_api_key = os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key=pinecone_api_key)

index_name = 'secret-hitler-strategy'
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=3072, # Replace with your model dimensions
        metric="cosine", # Replace with your model metric
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )
pinecone_index = pc.Index(index_name)