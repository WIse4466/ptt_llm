import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

# 傳入看板網址，抓取網頁內容，自動通過18歲驗證，回傳HTML原始碼
def get_html(url: str) -> str:
    session = requests.Session()
    payload = {
        "from": url,
        "yes": "yes"
    }
    session.post("https://www.ptt.cc/ask/over18", data=payload)
    response = session.get(url)
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
    article_soup = html_soup.find('div', class_='bbs-screen bbs-content')
    title = article_soup.find_all('span', class_='article-meta-value')[2].text
    author = article_soup.find_all('span', class_='article-meta-value')[0].text.strip(')').split('(')[0]
    time_str = article_soup.find_all('span', class_='article-meta-value')[3].text
    dt = datetime.strptime(time_str, "%a %b %d %H:%M:%S %Y")
    dt = dt.replace(tzinfo=ZoneInfo("Asia/Taipei"))
    post_time = dt.strftime("%Y-%m-%d %H:%M:%S")

    result = []
    for element in article_soup.children:
        if element.name not in ["div", "span"]:
            text = element.get_text(strip=True) if element.name == "a" else str(element).strip()
            if text:
                result.append(text)
    content = "\n".join(result).strip('-')

    data = {
        'title': title,
        'author': author,
        'post_time': post_time,
        'content': content,
    }
    return data

# 傳入看板名稱，回傳最新一頁的文章
def ptt_scrape(board: str) -> list:
    board_url = 'https://www.ptt.cc/bbs/' + board + '/index.html'
    board_html = get_html(board_url)
    article_urls = get_urls_from_board_html(board_html)
    article_datas = []
    for article_url in article_urls:
        article_html = get_html(article_url)
        article_data = get_data_from_article_html(article_html)
        article_data.update({'board': board})
        article_datas.append(article_data)
    return article_datas

if __name__ == "__main__":
    article_datas = ptt_scrape("Stock")
    for article_data in article_datas:
        print(article_data)