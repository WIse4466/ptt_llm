# celery_app/data_processing.py

import time
import random
from math import ceil
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pydantic import SecretStr
from langchain_core.documents import Document
from env_settings import EnvSettings
from article.models import Article

# 引入 Celery app
from config.celery import app

env_settings = EnvSettings()

BATCH_SIZE = 50
MAX_RETRIES = 5
BASE_DELAY = 2

def retry_with_backoff(func, *args, **kwargs):
    """
    重試機制：遇到 API 限制或連線錯誤時自動等待並重試
    """
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            if "ResourceExhausted" in error_msg or "429" in error_msg or "503" in error_msg:
                delay = BASE_DELAY * (2 ** attempt) + random.uniform(0, 1)
                print(f"[API Retry] Attempt {attempt+1}/{MAX_RETRIES} failed. Retrying in {delay:.2f}s...")
                time.sleep(delay)
            else:
                raise e
    raise RuntimeError("Max retries reached for embedding request")

@app.task
def store_data_in_pinecone(article_id_list: list):
    """
    Celery 任務：將指定的文章 ID 列表進行向量化並存入 Pinecone
    """
    
    # 如果沒有新文章，直接結束，避免浪費資源
    if not article_id_list:
        print("No new articles to vectorize.")
        return "No new articles."

    print(f"[Celery] Starting vectorization for {len(article_id_list)} articles...")
    
    # 初始化 Pinecone 與 Embedding 模型
    vector_store = PineconeVectorStore(
        index=Pinecone(api_key=env_settings.PINECONE_API_KEY).Index(env_settings.PINECONE_INDEX_NAME),
        embedding=GoogleGenerativeAIEmbeddings(
            model=env_settings.GOOGLE_EMBEDDINGS_MODEL,
            google_api_key=SecretStr(env_settings.GOOGLE_API_KEY),
        ),
    )

    documents = []
    # 設定文字切割器
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)

    # 從資料庫取出文章
    articles = Article.objects.filter(id__in=article_id_list).all()
    
    for article in articles:
        # 切割文章內容
        chunks = text_splitter.split_text(article.content)
        for i, chunk in enumerate(chunks):
            documents.append(Document(
                page_content=chunk,
                metadata={
                    "article_id": article.id,
                    "board": article.board,
                    "title": article.title,
                    "author": article.author,
                    "post_time": str(article.post_time),
                    "url": article.url,
                    "chunk_index": i
                }
            ))

    # 分批上傳 (Batch Upload)
    if documents:
        total_batches = ceil(len(documents) / BATCH_SIZE)
        for i in range(total_batches):
            batch_docs = documents[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
            retry_with_backoff(vector_store.add_documents, documents=batch_docs)
            print(f"[Batch {i+1}/{total_batches}] Uploaded {len(batch_docs)} docs")
    
    print("[Celery] Vectorization task completed successfully.")
    return f"Processed {len(documents)} chunks."