# PTT LLM 專案開發日誌 (2026-03-17)

本專案於今日完成了現代化 React 前端介面的建置，並成功打通了從 **PTT 文章爬取 -> 向量化存儲 -> RAG 語意搜尋 -> AI 生成回答** 的完整流程。

---

## 🚀 1. 新增功能與架構調整

### 前端介面 (React + Vite + TypeScript)
- **智慧搜尋 (RAG Search)**：仿 AI 助手設計，支持大型搜尋框、即時 Loading 動態、與 AI 分析結果展示。
- **數據儀表板 (Dashboard)**：整合 **Chart.js**，視覺化呈現 PTT 看板的文章分佈與每日發文趨勢。
- **美學設計**：採用簡潔的藍灰色調，實作了響應式佈局 (Responsive Design) 與平滑的過渡動畫 (Fade-in)。
- **技術棧**：React 19, Vite, Lucide React (圖標), react-markdown, react-chartjs-2, Axios。

### 後端 API 擴充 (`article/views.py`)
- **統計 API 升級**：擴充 `ArticleStatisticsView`，新增 `board_distribution` (看板分佈) 與 `daily_counts` (每日發文趨勢) 數據回傳，支援前端圖表渲染。

---

## 🛠 2. 遇到的挑戰與解決方案 (Debugging)

在開發過程中，我們遇到了幾個關鍵技術難題，並逐一排除：

### 🔴 問題 1：前端全白畫面 (White Screen)
- **現象**：啟動 `npm run dev` 後，瀏覽器畫面完全空白，Console 報錯 `Uncaught SyntaxError: The requested module '/src/types/index.ts' does not provide an export named 'Article'`。
- **原因**：Vite 在處理純 TypeScript `interface` 匯出時，有時會因為模組轉換 (ESM) 失敗而找不到匯出項。
- **修復**：
    1. 在 `types/index.ts` 中加入 `export const VERSION = '1.0.0'` 強迫其被識別為 JS 模組。
    2. 在匯入時使用 `import type` 關鍵字，明確告訴 Vite 這只是類型定義。
    3. 將 `react-markdown` 的匯入方式修正為更穩健的預設匯入。

### 🔴 問題 2：RAG 搜尋回傳 500 Internal Server Error
這是本次開發中最複雜的連鎖問題，包含三個層次：

#### (A) 模型名稱不匹配 (Model Not Found)
- **問題**：預設使用的 `models/text-embedding-004` 在該帳號的 API 權限下找不到。
- **解決**：執行 `genai.list_models()` 腳本，確認可用模型名稱為 **`models/gemini-embedding-001`**。

#### (B) 向量維度不匹配 (Vector Dimension Mismatch)
- **問題**：Pinecone 索引設定為 **768 維度**，但 `models/gemini-embedding-001` 預設回傳 **3072 維度**，導致 Pinecone 拒絕請求。
- **解決**：在 `article/rag_query.py` 中建立自定義的 `SafeGoogleEmbeddings` 類別，直接呼叫 Google SDK 並設定 **`output_dimensionality=768`**，強制進行維度縮減。

#### (C) API 額度與版本限制 (Resource Exhausted)
- **問題**：`gemini-2.0-flash` 模型因免費額度限制或配額未開放導致 429 錯誤。
- **解決**：根據使用者建議，將 Chat 模型更換為配額較充裕的 **`models/gemini-3.1-flash-lite-preview`**。

---

## 🎯 3. 最終成果驗證
經由測試腳本 `test_rag.py` 驗證，系統目前能穩定完成以下流程：
1. **問題向量化**：將使用者提問轉為 768 維向量。
2. **語意檢索**：從 Pinecone 找出相似的文章 ID。
3. **資料對接**：從 MariaDB 撈取文章內文。
4. **AI 生成**：透過 `gemini-3.1-flash-lite` 產出繁體中文的輿情分析報告。

---

## 📝 4. 維護建議
- **API Key 管理**：請確保 `.env` 中的 `GOOGLE_API_KEY` 與 `PINECONE_API_KEY` 有效。
- **模型監控**：若未來配額變動，可視情況將 `rag_query.py` 中的模型換回 `gemini-1.5-flash-latest`。
- **維度注意**：若未來重新建立 Pinecone 索引，維度需與程式碼中的 `output_dimensionality` 保持一致。

**開發者**：Gemini CLI & Wise
**日期**：2026-03-17
