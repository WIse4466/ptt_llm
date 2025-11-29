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

# 確保 Python 找得到專案根目錄
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# 設定 Django 的設定檔路徑 (您的專案名稱是 config)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

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
    try:
        meta_values = main_content.find_all('span', class_='article-meta-value')
        if len(meta_values) < 4: 
            return None # 資料不完整就跳過
        
        title = meta_values[2].text
        author = meta_values[0].text.strip(')').split('(')[0]
        time_str = meta_values[3].text
        
        dt = datetime.strptime(time_str, "%a %b %d %H:%M:%S %Y")
        dt = dt.replace(tzinfo=ZoneInfo("Asia/Taipei"))
        post_time = dt.strftime("%Y-%m-%d %H:%M:%S")

        # 這裡用 main_content 比較穩，因為 bbs-screen bbs-content 包含太多雜訊
        content_text = main_content.text
        # 簡單清理 (保留您的邏輯精神，但避免複雜操作出錯)
        content = content_text.split("※ 發信站")[0] 
        
        data = {
            'title': title,
            'author': author,
            'post_time': post_time,
            'content': content,
        }
        return data
    except Exception as e:
        print(f"解析文章錯誤: {e}")
        return None

# 傳入看板名稱，回傳最新一頁的文章
def ptt_scrape(board: str) -> list:
    # 這裡記得補上斜線
    board_url = 'https://www.ptt.cc/bbs/' + board + '/index.html'
    print(f"開始爬取: {board_url}")
    
    try:
        board_html = get_html(board_url)
        article_urls = get_urls_from_board_html(board_html)
    except Exception as e:
        print(f"爬取看板首頁失敗: {e}")
        return []

    article_datas = []
    for article_url in article_urls:
        print(f"正在爬取文章: {article_url}")
        try:
            # 加上延遲，避免太快被鎖 IP
            time.sleep(1) 
            article_html = get_html(article_url)
            article_data = get_data_from_article_html(article_html)
            if article_data:
                article_data.update({
                    'board': board,
                    'url': article_url
                })
                article_datas.append(article_data)
        except Exception as e:
            print(f"跳過異常文章: {e}")
            continue
            
    return article_datas

if __name__ == "__main__":
    # 從 article app 引入模型 (記得確認您的 app 名稱是否為 article)
    from article.models import Article
    
    # 爬取 Stock 板
    article_datas = ptt_scrape("Stock")
    
    print(f"準備寫入 {len(article_datas)} 筆資料...")

    for article_data in article_datas:
        try:
            # 使用 update_or_create 避免重複寫入 (如果網址相同就更新，不同就建立)
            # 這比 try...except IntegrityError 更聰明
            obj, created = Article.objects.update_or_create(
                url=article_data['url'], # 以網址作為判斷標準
                defaults={
                    'board': article_data['board'],
                    'title': article_data['title'],
                    'author': article_data['author'],
                    'content': article_data['content'],
                    'post_time': article_data['post_time']
                }
            )
            status = "新增" if created else "更新"
            print(f"[{status}] {article_data['title']}")
            
        except Exception as e:
            print(f"寫入錯誤: {e}")

    print('完成所有寫入!')