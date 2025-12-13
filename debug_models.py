# debug_models.py
import os
import google.generativeai as genai
from env_settings import EnvSettings

# 1. 讀取環境變數
env = EnvSettings()
api_key = env.GOOGLE_API_KEY

print(f"-------- Debug Info --------")
print(f"API Key (前5碼): {api_key[:5]}...")
print(f"----------------------------")

# 2. 設定 Google AI
genai.configure(api_key=api_key)

# 3. 列出所有可用模型
print("正在連線 Google 查詢可用模型...")
try:
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            available_models.append(m.name)
    
    if not available_models:
        print("❌ 連線成功，但沒有找到任何支援 generateContent 的模型。")
        print("可能原因：API Key 所在的 Google Cloud 專案沒有啟用 Generative AI API。")
    else:
        print(f"\n✅ 成功！您的 API Key 可以使用以上模型。")
        print("請將 rag_query.py 裡的 model 名稱改成上面列表中的其中一個（通常是 models/ 去掉後的名字）。")

except Exception as e:
    print(f"\n❌ 連線失敗！錯誤訊息：")
    print(e)