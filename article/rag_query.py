import traceback
import asyncio
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from pydantic import SecretStr
from article.models import Article
from log_app.models import Log
from env_settings import EnvSettings

env_settings = EnvSettings()

def run_rag_query(question, top_k):
    """
    執行 RAG 流程：
    1. 將問題轉向量 -> 搜尋 Pinecone
    2. 找出對應的 MariaDB 文章
    3. 組合 Prompt -> 呼叫 Gemini 生成回答
    """
    
    # 1. 搜尋 Pinecone
    try:
        # 解決 Django 環境下 asyncio loop 的問題
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        vector_store = PineconeVectorStore(
            index=Pinecone(api_key=env_settings.PINECONE_API_KEY).Index(env_settings.PINECONE_INDEX_NAME),
            embedding=GoogleGenerativeAIEmbeddings(
                model=env_settings.GOOGLE_EMBEDDINGS_MODEL,
                google_api_key=SecretStr(env_settings.GOOGLE_API_KEY)
            )
        )
        # 執行相似度搜尋
        top_k_results = vector_store.similarity_search_with_score(question, k=top_k)
    
    except Exception as e:
        error_msg = f"查詢 Pinecone 發生錯誤: {e}"
        Log.objects.create(level='ERROR', category='rag-search', message=error_msg, traceback=traceback.format_exc())
        return {"error": error_msg}

    # 2. 從資料庫撈取文章內容
    try:
        # 從 metadata 取出 article_id
        match_ids = [match[0].metadata['article_id'] for match in top_k_results]
        
        # 這裡要注意順序：Pinecone 回傳的順序是依相似度排序，但 SQL filter(id__in=...) 不保證順序
        # 為了精準度，我們先撈出來，再依照 match_ids 的順序排好
        articles_queryset = Article.objects.filter(id__in=match_ids)
        articles_dict = {a.id: a for a in articles_queryset}
        related_articles = [articles_dict[mid] for mid in match_ids if mid in articles_dict]

        # 組合給 LLM 看的文本 (避免過長，簡單截斷)
        merge_text = "\n".join(
            [f"標題:{a.title}\n內文:{a.content[:500]}..." for a in related_articles]
        )
        
        # 簡單的防呆，避免爆 Token
        if len(merge_text) > 100000:
            return {"error": "檢索到的文章總字數過長，請減少 top_k"}

    except Exception as e:
        error_msg = f"資料庫撈取文章失敗: {e}"
        Log.objects.create(level='ERROR', category='rag-db', message=error_msg, traceback=traceback.format_exc())
        return {"error": error_msg}

    # 3. 呼叫 Gemini 生成回答
    try:
        # 注意：建議先用 gemini-1.5-flash 比較穩定，若您有 2.0 權限可改為 gemini-2.0-flash
        model = ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            temperature=0.3, # 稍微有點創造力但不要太發散
            google_api_key=env_settings.GOOGLE_API_KEY,
        )
        
        prompt = PromptTemplate(
            input_variables=["merge_text", "question"],
            template="""
            你是一個專業的 PTT 輿情分析師。請根據以下 PTT 文章內容，用繁體中文回答使用者的問題。
            如果文章內容沒有提到相關資訊，請直接回答「找不到相關討論」。
            
            --- 參考文章 ---
            {merge_text}
            ---
            
            使用者問題：{question}
            """
        )
        
        chain = prompt | model
        response = chain.invoke({"merge_text": merge_text, "question": question})
        answer = response.content

        return {
            "question": question,
            "answer": answer,
            "related_articles": related_articles # 直接回傳 Model 物件列表，Serializer 會處理
        }

    except Exception as e:
        error_msg = f"LLM 生成回答失敗: {e}"
        Log.objects.create(level='ERROR', category='rag-llm', message=error_msg, traceback=traceback.format_exc())
        return {"error": error_msg}