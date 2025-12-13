
-----

# PTT LLM - PTT 輿情分析與 RAG 智慧問答系統

本專案是一個結合 **爬蟲 (Web Scraping)**、**向量資料庫 (Vector DB)** 與 **生成式 AI (GenAI)** 的全端應用程式。

系統會自動定時爬取 PTT 特定看板（如 Stock、Gossiping）的文章，將其儲存於 MariaDB，並透過 Embedding 模型轉為向量存入 Pinecone。使用者可以透過 API 詢問問題，系統將利用 **RAG (Retrieval-Augmented Generation)** 技術檢索相關文章，並由 Google Gemini 模型生成精準回答。

## ✨ 主要功能

  * **自動化爬蟲**：使用 Celery Beat 定時爬取 PTT 熱門看板文章與留言。
  * **非同步任務處理**：透過 Celery + Redis 處理爬蟲與向量化任務，避免阻塞網站運作。
  * **RAG 語意搜尋**：整合 LangChain 與 Pinecone，實現精準的文章語意檢索。
  * **AI 智慧問答**：串接 Google Gemini (Flash) 模型，根據爬取的輿情資料回答使用者問題。
  * **RESTful API**：使用 Django REST Framework 開發，並提供 Swagger 自動化文件。
  * **容器化部署**：支援 Docker Compose 一鍵部署所有服務 (Django, MariaDB, Redis, Celery)。

## 🛠️ 技術堆疊

  * **Backend**: Django, Django REST Framework
  * **Database**: MariaDB (SQL), Pinecone (Vector)
  * **Task Queue**: Celery, Redis
  * **AI / LLM**: Google Gemini API, LangChain
  * **DevOps**: Docker, Docker Compose, Poetry

-----

## 🚀 快速啟動 (Quick Start)

### 1\. 環境變數設定

在專案根目錄建立 `.env` 檔案，並填入以下必要資訊：

```ini
# Database & Redis
MYSQL_ROOT_PASSWORD=secret
MYSQL_DATABASE=ptt_llm
MYSQL_USER=user
MYSQL_PASSWORD=password
REDIS_HOST=redis

# Google Gemini API (前往 Google AI Studio 申請)
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_EMBEDDINGS_MODEL=models/embedding-001

# Pinecone Vector DB (前往 Pinecone Console 申請)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=your_index_name
```

### 2\. 啟動所有服務

執行以下指令，透過 Docker Compose 建置並啟動所有容器：

```bash
docker compose up --build -d
```

  * `--build`：強制重新建置映像檔（確保 Python 套件為最新）。
  * `-d`：在背景執行。

### 3\. 確認服務狀態

確保所有容器狀態皆為 `Up` 或 `healthy`：

```bash
docker compose ps
```

-----

## 📖 API 使用說明

服務啟動後，您可以透過瀏覽器訪問 Swagger UI 進行測試。

  * **Swagger 文件網址**：[http://127.0.0.1:8000/api/schema/doc/](http://127.0.0.1:8000/api/schema/doc/)

### 🔥 核心功能：AI 語意搜尋

  * **Endpoint**: `POST /api/search/`
  * **功能**：輸入問題，系統會檢索資料庫並回傳 AI 整理的答案及參考文章。
  * **範例請求 (JSON)**：
    ```json
    {
      "question": "最近大家對輝達(Nvidia)的看法如何？",
      "top_k": 3
    }
    ```

-----

## 🔧 開發與維護指令

### 查看日誌 (Logs)

```bash
# 查看 Django 網站日誌 (API 錯誤看這裡)
docker compose logs -f web

# 查看 Celery Worker 日誌 (爬蟲與向量化進度看這裡)
docker compose logs -f celery

# 查看 Celery Beat 排程日誌 (確認排程觸發看這裡)
docker compose logs -f celery-beat
```

### 資料庫遷移與管理

建議使用 `docker compose exec` 進入容器執行 Django 指令：

```bash
# 建立資料庫遷移檔
docker compose exec web python manage.py makemigrations

# 執行遷移 (更新資料庫結構)
docker compose exec web python manage.py migrate

# 建立後台管理員 (Superuser)
docker compose exec web python manage.py createsuperuser
```

### 手動觸發爬蟲測試

如果您不想等待排程，可以手動觸發 Celery 任務：

1.  進入 Django Shell：

    ```bash
    docker compose exec web python manage.py shell
    ```

2.  輸入 Python 程式碼手動發送任務：

    ```python
    from celery_app.tasks import period_send_ptt_scrape_task
    # 非同步執行任務
    period_send_ptt_scrape_task.delay()
    exit()
    ```

### 停止服務

```bash
docker compose down
```

### 檢視可用模型
```bash
docker compose exec web pip show langchain-google-genai
```
-----

## 📁 專案結構

```text
.
├── article/             # Django App: 文章模型、爬蟲邏輯、RAG 搜尋
│   ├── scraper.py       # PTT 爬蟲主程式
│   ├── rag_query.py     # RAG (Pinecone + Gemini) 核心邏輯
│   └── views.py         # API Views
├── celery_app/          # Celery 任務定義
│   ├── tasks.py         # 排程任務入口
│   └── data_processing.py # 向量化處理任務
├── config/              # Django 專案設定 (Settings, Celery config)
├── docker-compose.yml   # Docker 服務編排
├── Dockerfile           # Python 環境建置
└── pyproject.toml       # Poetry 套件管理
```