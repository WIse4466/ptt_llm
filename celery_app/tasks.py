from celery import chain
from config.celery import app
from article.scraper import ptt_scrape  # <--- 修正這行
from celery_app.data_processing import store_data_in_pinecone

@app.task
def scrape_task(board):
    return ptt_scrape(board)

@app.task
def period_send_ptt_scrape_task():
    board_list = ['Stock', 'Gossiping']
    for board in board_list:
        task_chain = chain(
            scrape_task.s(board),
            store_data_in_pinecone.s()
        )
        task_chain.apply_async()
        print(f"Sent task chain for {board}")