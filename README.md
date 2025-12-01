# PTT LLM 專案

本專案使用 Django、Celery 與 Docker，建立一個可定時爬取 PTT 特定看板文章、留言並存入資料庫的系統。

---

## 需求

- Docker
- Docker Compose

---

## 快速啟動

1. **啟動所有服務**

   在專案根目錄執行以下指令，即可透過 Docker Compose 一次性建置並啟動所有服務（包含網站、資料庫、Redis、Celery Worker 和 Celery Beat 排程器）。

   ```bash
   docker compose up --build -d
   ```
   - `--build`：在初次啟動或修改過程式碼後，強制重新建置映像檔。
   - `-d`：在背景執行服務。

2. **查看服務狀態**

   使用此指令來確認所有容器是否正常運行（狀態應為 `running` 或 `healthy`）。

   ```bash
   docker compose ps
   ```

3. **停止所有服務**

   當您想停止專案時，執行以下指令：

   ```bash
   docker compose down
   ```

---

## 如何使用

### 查看日誌

您可以查看特定服務的日誌來了解其運行狀況或進行除錯。

```bash
# 查看 Web 服務日誌
docker compose logs django_web

# 即時追蹤 Celery Worker 日誌
docker compose logs -f celery

# 查看 Celery Beat 排程日誌
docker compose logs -f celery-beat
```

### 執行 Django 管理指令

當您需要執行 `makemigrations` 或 `createsuperuser` 等指令時，建議進入 `django_web` 容器中執行，以確保環境一致。

```bash
# 1. 進入 django_web 容器的 shell
docker exec -it django_web sh

# 2. 在容器內執行您需要的指令
# 例如：建立新的資料庫遷移檔案
python manage.py makemigrations

# 例如：建立後台管理員帳號
python manage.py createsuperuser

# 3. 完成後，輸入 exit 即可退出容器
exit
```

### 手動觸發爬蟲測試

如果您想立即執行一次爬蟲任務而不等待排程，可以進入 `celery` 容器來手動執行。

```bash
# 1. 進入 celery 容器的 shell
docker exec -it celery sh

# 2. 在容器內執行 scraper.py 腳本
# 這會爬取 Stock 板塊作為測試
python celery_app/scraper.py

# 3. 完成後，輸入 exit 即可退出容器
exit
```
