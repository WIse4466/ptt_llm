import os
import sys
import django
import requests
import time
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------
# 1. 設定 Django 環境 (必須在 import models 之前)
# ---------------------------------------------------------
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# ---------------------------------------------------------
# 2. 引入 Models
# ---------------------------------------------------------
from article.models import Article, Comment
from log_app.models import Log
# 注意：這裡不再引入 store_data_in_pinecone，因為將由 Celery tasks.py 負責串接

# ---------------------------------------------------------
# 3. 爬蟲核心函式
# ---------------------------------------------------------

def get_html(url: str) -> str:
    """取得網頁內容，包含偽裝 Headers 與重試機制"""
    session = requests.Session()
    
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.ptt.cc/'
    })

    # 直接設定 Cookie 通過 18 歲驗證
    session.cookies.set('over18', '1')
    
    response = session.get(url, timeout=10)
    return response.text

def get_urls_from_board_html(html: str) -> list:
    """解析看板列表頁，取得文章連結"""
    html_soup = BeautifulSoup(html, 'html.parser')
    r_ent_all = html_soup.find_all('div', class_='r-ent')
    urls = []
    for r_ent in r_ent_all:
        a_tag = r_ent.find('a')
        if a_tag and a_tag.get('href'):
            urls.append('https://www.ptt.cc' + a_tag['href'])
    return urls

def get_data_from_article_html(html: str) -> dict:
    """解析單篇文章內容與推文"""
    html_soup = BeautifulSoup(html, 'html.parser')
    
    main_content = html_soup.find('div', id='main-content')
    if not main_content:
        return None
    
    # 檢查 Meta 資訊是否完整
    meta_values = main_content.find_all('span', class_='article-meta-value')
    if len(meta_values) < 4: 
        return None 
    
    author = meta_values[0].text.strip(')').split('(')[0]
    title = meta_values[2].text
    time_str = meta_values[3].text
    
    # --- 日期時間處理 (包含年份補全邏輯) ---
    try:
        dt = datetime.strptime(time_str, "%a %b %d %H:%M:%S %Y")
    except ValueError:
        # PTT 有些舊文章或特殊格式可能沒有年份，嘗試補上今年
        try:
            current_year = datetime.now().year
            time_str_with_year = f"{time_str} {current_year}"
            dt = datetime.strptime(time_str_with_year, "%a %b %d %H:%M:%S %Y")
        except ValueError:
            # 如果真的解析失敗，就用當下時間，避免程式崩潰
            dt = datetime.now()

    # 設定時區
    dt = dt.replace(tzinfo=ZoneInfo("Asia/Taipei"))
    post_time = dt

    # --- 解析推文 ---
    comments = []
    push_elements = main_content.find_all('div', class_='push')
    
    for push in push_elements:
        try:
            tag = push.find('span', class_='push-tag').text.strip()
            user_id = push.find('span', class_='push-userid').text.strip()
            content = push.find('span', class_='push-content').text.strip(': ')
            ip_datetime = push.find('span', class_='push-ipdatetime').text.strip()
            
            comments.append({
                'tag': tag,
                'user_id': user_id,
                'content': content,
                'ip_datetime': ip_datetime
            })
        except AttributeError:
            continue

    # --- 處理內文 ---
    # 移除推文區塊，只保留本文
    full_text = main_content.text
    content = full_text.split("※ 發信站")[0]

    data = {
        'title': title,
        'author': author,
        'post_time': post_time,
        'content': content,
        'comments': comments
    }
    return data

def ptt_scrape(board: str) -> list:
    """
    爬取指定看板的最新一頁
    回傳: list (本次新增的文章 ID 列表，供 RAG 使用)
    """
    print(f"[INFO] Start scraping board: {board}")
    Log.objects.create(level='INFO', category=f'scrape-{board}', message=f'Start scraping {board}')
    
    board_url = 'https://www.ptt.cc/bbs/' + board + '/index.html'
    
    try:
        board_html = get_html(board_url)
        article_urls = get_urls_from_board_html(board_html)
    except Exception as e:
        error_msg = f"Failed to fetch board index: {e}"
        print(f"[ERROR] {error_msg}")
        Log.objects.create(level='ERROR', category=f'scrape-{board}', message=error_msg, traceback=traceback.format_exc())
        return []

    new_article_ids = [] # 用來存本次新增的文章 ID
    update_count = 0
    create_count = 0
    
    for article_url in article_urls:
        try:
            time.sleep(0.5) # 禮貌性延遲
            print(f"[INFO] Processing: {article_url}")
            
            article_html = get_html(article_url)
            article_data = get_data_from_article_html(article_html)

            if not article_data:
                print(f"[WARN] Failed to parse or format incorrect: {article_url}")
                Log.objects.create(level='WARNING', category=f'scrape-{board}', message=f'Parse failed: {article_url}')
                continue

            # 1. 寫入文章
            article_obj, created = Article.objects.update_or_create(
                url=article_url,
                defaults={
                    'board': board,
                    'title': article_data['title'],
                    'author': article_data['author'],
                    'content': article_data['content'],
                    'post_time': article_data['post_time']
                }
            )

            # 2. 統計與收集 ID
            if created:
                create_count += 1
                new_article_ids.append(article_obj.id) # 只有新文章才回傳 ID
            else:
                update_count += 1

            # 3. 處理推文
            comments_data = article_data.get('comments', [])
            if comments_data:
                # 先刪除舊推文，避免重複
                Comment.objects.filter(article=article_obj).delete()
                
                comments_objects = [
                    Comment(
                        article=article_obj,
                        tag=c['tag'],
                        user_id=c['user_id'],
                        content=c['content'],
                        ip_datetime=c['ip_datetime']
                    ) for c in comments_data
                ]
                # 批次寫入
                Comment.objects.bulk_create(comments_objects)

        except Exception as e:
            print(f"[ERROR] Exception: {e}")
            Log.objects.create(
                level='ERROR',
                category=f'scrape-{board}',
                message=f"Error processing article {article_url}: {e}",
                traceback=traceback.format_exc()
            )
            continue
    
    summary = f'Scrape {board} completed. Created: {create_count}, Updated: {update_count}'
    print(f"[SUCCESS] {summary}")
    Log.objects.create(level='INFO', category=f'scrape-{board}', message=summary)
    
    return new_article_ids

# ---------------------------------------------------------
# 4. 主程式執行區塊 (僅供手動測試爬蟲功能)
# ---------------------------------------------------------
if __name__ == "__main__":
    # 測試爬取 Stock 板
    # 注意：此處手動執行不會觸發 Celery 的向量化任務
    print("[TEST] Starting manual scrape test...")
    target_board = "Stock"
    ids = ptt_scrape(target_board)
    print(f"[TEST] Manual scrape finished. New Article IDs: {ids}")