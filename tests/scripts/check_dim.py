import google.generativeai as genai
import os

os.environ['GOOGLE_API_KEY'] = "AIzaSyDpe4oEuZXNwod6Cuqpx31g5pcEPnVMtFw"
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

text = "這是一個測試"
result = genai.embed_content(model="models/gemini-embedding-001", content=text)
print(f"models/gemini-embedding-001 維度: {len(result['embedding'])}")

try:
    result2 = genai.embed_content(model="models/gemini-embedding-001", content=text, output_dimensionality=768)
    print(f"models/gemini-embedding-001 (指定768) 維度: {len(result2['embedding'])}")
except Exception as e:
    print(f"❌ 不支援指定維度: {e}")
