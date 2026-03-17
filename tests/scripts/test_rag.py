import os
import django
import sys
from pathlib import Path

# 修正：將專案根目錄加入 Python 搜尋路徑
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

# 1. 關鍵：手動設定環境變數，確保模型名稱正確
os.environ['GOOGLE_EMBEDDINGS_MODEL'] = "models/gemini-embedding-001"
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from article.rag_query import run_rag_query

# 2. 模擬 RAG 查詢
question = "最近台股在討論什麼？"
top_k = 3

print(f"--- 正在測試 RAG 查詢 (模型: {os.environ['GOOGLE_EMBEDDINGS_MODEL']}) ---")
try:
    result = run_rag_query(question, top_k)
    if "error" in result:
        print(f"❌ 查詢失敗: {result['error']}")
    else:
        print(f"✅ 查詢成功!")
        print(f"回答內容: {result['answer'][:300]}...")
        print(f"參考文章數量: {len(result['related_articles'])}")
except Exception as e:
    import traceback
    print(f"🔥 發生嚴重崩潰: {e}")
    traceback.print_exc()
