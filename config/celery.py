import os
from celery import Celery

# 1. 設定 Django 環境變數
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 2. 動態決定 Redis Host
# 如果在 Docker 內 (有環境變數)，用 'redis'；如果在 Mac 本機，用 '127.0.0.1'
REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
redis_url = f'redis://{REDIS_HOST}:6379/0'

# 3. 初始化 Celery App
app = Celery("config", broker=redis_url, backend=redis_url)

# 4. 讀取 Django settings 中的設定 (例如時區等)
app.config_from_object('django.conf:settings', namespace='CELERY')

# 5. 自動探索並載入任務
app.autodiscover_tasks()

# 明確指定要載入的任務模組
app.conf.imports = [
    "celery_app.tasks",           # 包含爬蟲與排程的主邏輯
    "celery_app.data_processing", # 包含 Pinecone 向量化邏輯
]

# 6. 設定排程 (Beat Schedule)
app.conf.beat_schedule = {
    'scrape-every-hour': {
        # 注意：這裡指向的是 tasks.py，因為那是我們定義 @app.task 的地方
        'task': 'celery_app.tasks.period_send_ptt_scrape_task', 
        
        # 設定執行頻率 (秒)
        'schedule': 600, 
    }
}