from celery import Celery
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

app = Celery("config", broker="redis://redis:6379/0", backend="redis://redis:6379/0")
app.autodiscover_tasks()

app.conf.imports = [
    "celery_app.scraper",
]

app.conf.beat_schedule = {
    'scrape-every-hour': {
        'task': 'celery_app.scraper.period_send_ptt_scrape_task', # 指定任務位置
        'schedule': 3600, # 定時3600秒
    }
}
