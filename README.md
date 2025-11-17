# ptt_llm

---

## 開發環境啟用（Development）

本專案支援 Docker 快速啟用與本地 Poetry 開發模式。

### 1. 安裝依賴（首次啟用）

如果您是第一次（或 `git pull` 更新後）
使用本專案，請先安裝/同步所有依賴套件。

```bash
# 我們使用 --no-root，因為這是一個「應用程式」而非「套件」
# 這會讀取 poetry.lock 檔案，並安裝所有依賴
poetry install --no-root
```

### 2. 啟用服務
#### 使用 Docker
此指令會自動
1. 啟動 MariaDB 資料庫。
2. 執行 migrate 同步資料庫結構。
3. 啟動 Django 開發伺服器。
```bash
docker compose up --build
```
啟動成功後，請在瀏覽器開啟：http://localhost:8000

注意：若要停止服務，請在終端機按下 Ctrl + C。