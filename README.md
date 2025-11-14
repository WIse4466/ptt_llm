# ptt_llm

---

## 開發環境啟用（Development）

本專案使用 Poetry 管理依賴與虛擬環境。

### 1. 安裝依賴（首次啟用）

如果您是第一次（或 `git pull` 更新後）
使用本專案，請先安裝/同步所有依賴套件。

```bash
# 我們使用 --no-root，因為這是一個「應用程式」而非「套件」
# 這會讀取 poetry.lock 檔案，並安裝所有依賴
poetry install --no-root
```

### 2. 啟用服務
```bash
# 遷移並同步資料庫 建立 Django 所需的資料表
poetry run python manage.py migrate
```
```bash
# 運行伺服器 即時預覽
poetry run python manage.py runserver
```