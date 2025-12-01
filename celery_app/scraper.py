import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import os
import django
import sys

from config.celery import app

# 設定 Django 的設定檔路徑 (您的專案名稱是 config)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# 將模型導入移到檔案頂部
from article.models import Article, Comment
from log_app.models import Log
import traceback

# 定義 Celery 任務
@app.task()
def period_send_ptt_scrape_task():
    board_list = ['Gossiping', 'NBA', 'Stock', 'LoL', 'home-sale']
    print(f"Celery 任務開始執行，爬取看板: {', '.join(board_list)}")
    for board in board_list:
        try:
            article_ids = ptt_scrape(board)
            print(f"看板 [{board}] 爬取完成，寫入 {len(article_ids)} 篇文章。")
        except Exception as e:
            Log.objects.create(
                level='ERROR',
                category=f'scrape-{board}',
                message=f"爬取看板 [{board}] 發生未預期錯誤: {e}",
                traceback=traceback.format_exc()
            )

# 傳入看板網址，抓取網頁內容，自動通過18歲驗證，回傳HTML原始碼
def get_html(url: str) -> str:
    session = requests.Session()
    # 設定重試機制：遇到被斷線時，自動重試 3 次，且每次間隔一段時間
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    # 偽裝成真人瀏覽器（這是通過 PTT 防火牆的關鍵）
    session.headers.update({
        'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.ptt.cc/'
    })

    # 18歲驗證
    session.cookies.set('over18', '1')
    
    response = session.get(url, timeout=10)
    return response.text

# 傳入看板的網頁內容(HTML)，提取所有文章的網址，回傳網址列表
def get_urls_from_board_html(html: str) -> list:
    html_soup = BeautifulSoup(html, 'html.parser')
    r_ent_all = html_soup.find_all('div', class_='r-ent')
    urls = []
    for r_ent in r_ent_all:
        if r_ent.find('a'):
            if r_ent.find('a')['href']:
                urls.append('https://www.ptt.cc' + r_ent.find('a')['href'])
    return urls

# 傳入文章的網頁內容(HTML)，提取標題、作者、發文時間與文章內容
def get_data_from_article_html(html: str) -> dict:
    html_soup = BeautifulSoup(html, 'html.parser')
    
    # 加入防呆機制，以免抓到 404 頁面時報錯
    main_content = html_soup.find('div', id='main-content')
    if not main_content:
        return None
    
    meta_values = main_content.find_all('span', class_='article-meta-value')
    if len(meta_values) < 4: 
        return None # 資料不完整就跳過
    
    title = meta_values[2].text
    author = meta_values[0].text.strip(')').split('(')[0]
    time_str = meta_values[3].text
    
    # 處理沒有年份的日期
    try:
        dt = datetime.strptime(time_str, "%a %b %d %H:%M:%S %Y")
    except ValueError:
        # 如果沒有年份，手動加上當年年份再試一次
        current_year = datetime.now().year
        time_str_with_year = f"{time_str} {current_year}"
        dt = datetime.strptime(time_str_with_year, "%a %b %d %H:%M:%S %Y")

    dt = dt.replace(tzinfo=ZoneInfo("Asia/Taipei"))
    post_time = dt

    # --- 解析推文 ---
    comments = []
    # 找出所有 class 為 push 的 div
    push_elements = main_content.find_all('div', class_='push')
    
    for push in push_elements:
        try:
            # 提取推文的四個欄位
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
            # 有些推文可能格式壞掉，跳過就好
            continue

    # --- 處理內文 ---
    # 為了避免內文包含到推文，我們將 main_content 轉成文字前，先把推文移除
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


# 傳入看板名稱，回傳最新一頁的文章
def ptt_scrape(board: str) -> list:
    Log.objects.create(level='INFO', category=f'scrape-{board}', message=f'開始爬取 {board}')
    
    board_url = 'https://www.ptt.cc/bbs/' + board + '/index.html'
    
    try:
        board_html = get_html(board_url)
        article_urls = get_urls_from_board_html(board_html)
    except Exception as e:
        Log.objects.create(
            level='ERROR',
            category=f'scrape-{board}',
            message=f"爬取看板首頁失敗: {e}",
            traceback=traceback.format_exc()
        )
        return []

    article_id_list = []
    update_count = 0
    create_count = 0
    
    for article_url in article_urls:
        try:
            time.sleep(0.5) 
            article_html = get_html(article_url)
            article_data = get_data_from_article_html(article_html)

            if not article_data:
                Log.objects.create(level='WARNING', category=f'scrape-{board}', message=f'從 {article_url} 解析資料失敗，可能為 404 或格式不符')
                continue

            # 使用 update_or_create 處理文章，並記錄是新增還是更新
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
            article_id_list.append(article_obj.id)
            if created:
                create_count += 1
            else:
                update_count += 1

            # 處理推文
            comments_data = article_data.get('comments', [])
            if comments_data:
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
                Comment.objects.bulk_create(comments_objects)

        except Exception as e:
            Log.objects.create(
                level='ERROR',
                category=f'scrape-{board}',
                message=f"處理文章 {article_url} 時發生錯誤: {e}",
                traceback=traceback.format_exc()
            )
            continue
    
    Log.objects.create(
        level='INFO',
        category=f'scrape-{board}',
        message=f'爬取 {board} 完成，共處理 {len(article_urls)} 篇文章。新增 {create_count} 筆，更新 {update_count} 筆。'
    )
    return article_id_list

if __name__ == "__main__":
    # 測試爬取 Gossiping 板
    article_ids = ptt_scrape("Stock")
    print(f'寫入完成! 共處理 {len(article_ids)} 篇文章。')

if __name__ == "__main__":
    # 測試爬取 Gossiping 板
    article_ids = ptt_scrape("Gossiping")
    print(f'寫入完成! 共處理 {len(article_ids)} 篇文章。')