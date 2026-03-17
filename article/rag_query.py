import traceback
import asyncio
import google.generativeai as genai
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SecretStr
from article.models import Article
from log_app.models import Log
from env_settings import EnvSettings

env_settings = EnvSettings()

class SafeGoogleEmbeddings:
    """
    自定義 Embedding 類別，直接呼叫 Google SDK 以確保維度縮減 (Dimension Reduction)。
    這解決了 LangChain 整合包在某些版本中可能不傳遞 output_dimensionality 參數的問題。
    """
    def __init__(self, api_key, model="models/gemini-embedding-001"):
        self.model = model
        genai.configure(api_key=api_key)

    def embed_documents(self, texts):
        # 批量處理
        results = genai.embed_content(
            model=self.model,
            content=texts,
            task_type="retrieval_document",
            output_dimensionality=768 # 強制 768 維度，配合您的 Pinecone 索引
        )
        return results['embeddings']

    def embed_query(self, text):
        # 單筆處理
        result = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_query",
            output_dimensionality=768 # 強制 768 維度，配合您的 Pinecone 索引
        )
        return result['embedding']

def run_rag_query(question, top_k):
    """
    執行 RAG 流程。
    """
    # 1. 搜尋 Pinecone
    try:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        # 使用自定義的 SafeGoogleEmbeddings 確保維度與 Pinecone Index (768) 匹配
        embeddings = SafeGoogleEmbeddings(api_key=env_settings.GOOGLE_API_KEY)

        vector_store = PineconeVectorStore(
            index=Pinecone(api_key=env_settings.PINECONE_API_KEY).Index(env_settings.PINECONE_INDEX_NAME),
            embedding=embeddings
        )
        
        top_k_results = vector_store.similarity_search_with_score(question, k=top_k)
    
    except Exception as e:
        error_msg = f"查詢 Pinecone 發生錯誤: {e}"
        Log.objects.create(level='ERROR', category='rag-search', message=error_msg, traceback=traceback.format_exc())
        return {"error": error_msg}

    # 2. 從資料庫撈取文章內容
    try:
        match_ids = [match[0].metadata['article_id'] for match in top_k_results]
        articles_queryset = Article.objects.filter(id__in=match_ids)
        articles_dict = {a.id: a for a in articles_queryset}
        related_articles = [articles_dict[mid] for mid in match_ids if mid in articles_dict]

        if not related_articles:
            return {
                "question": question,
                "answer": "抱歉，資料庫中目前沒有相關討論。",
                "related_articles": []
            }

        merge_text = "\n".join([f"標題:{a.title}\n內文:{a.content[:500]}..." for a in related_articles])

    except Exception as e:
        error_msg = f"資料庫撈取文章失敗: {e}"
        Log.objects.create(level='ERROR', category='rag-db', message=error_msg, traceback=traceback.format_exc())
        return {"error": error_msg}

    # 3. 呼叫 Gemini 生成回答
    try:
        # 使用您指定的具有配額的模型
        model = ChatGoogleGenerativeAI(
            model="models/gemini-3.1-flash-lite-preview",
            temperature=0.3,
            google_api_key=SecretStr(env_settings.GOOGLE_API_KEY),
        )
        
        prompt = PromptTemplate(
            input_variables=["merge_text", "question"],
            template="""
            你是一個專業的 PTT 輿情分析師。請根據以下 PTT 文章內容，用繁體中文回答使用者的問題。
            
            --- 參考文章 ---
            {merge_text}
            ---
            
            使用者問題：{question}
            """
        )
        
        chain = prompt | model
        response = chain.invoke({"merge_text": merge_text, "question": question})
        return {
            "question": question,
            "answer": response.content,
            "related_articles": related_articles
        }

    except Exception as e:
        error_msg = f"LLM 錯誤: {e}"
        Log.objects.create(level='ERROR', category='rag-llm', message=error_msg, traceback=traceback.format_exc())
        return {"error": error_msg}
