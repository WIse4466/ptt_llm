import os
import django
import sys
from pathlib import Path
import google.generativeai as genai

# 加入專案根目錄
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

# 1. 設定 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from env_settings import EnvSettings
env_settings = EnvSettings()

print(f"--- 正在列出可用模型 (API Key: {env_settings.GOOGLE_API_KEY[:10]}...) ---")
genai.configure(api_key=env_settings.GOOGLE_API_KEY)

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ 可用的 Chat 模型: {m.name}")
except Exception as e:
    print(f"❌ 無法列出模型: {e}")
