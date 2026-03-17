import { useState, useEffect } from 'react';
import { Search, BarChart3, MessageSquare, Newspaper, Github } from 'lucide-react';
import SearchBar from './components/SearchBar';
import ResultView from './components/ResultView';
import Dashboard from './components/Dashboard';
import { searchArticles, getStatistics } from './services/api';
import type { SearchResponse, StatisticsResponse } from './types';

function App() {
  const [activeTab, setActiveTab] = useState<'search' | 'stats'>('search');
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [stats, setStats] = useState<StatisticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const data = await getStatistics();
        if (data) setStats(data);
      } catch (err) {
        console.error('Stats loading failed:', err);
      }
    };
    loadStats();
  }, []);

  const handleSearch = async (question: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await searchArticles(question);
      if (result && result.answer) {
        setSearchResult(result);
        setActiveTab('search');
      } else {
        setError('找不到相關答案。');
      }
    } catch (err) {
      setError('搜尋失敗，請確認 API 是否運作正常。');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-wrapper">
      <header className="app-header">
        <div className="app-logo">
          <MessageSquare size={26} color="#3b82f6" />
          <span>PTT LLM Pulse</span>
        </div>
        <nav className="app-nav">
          <button 
            className={`nav-item ${activeTab === 'search' ? 'active' : ''}`}
            onClick={() => setActiveTab('search')}
          >
            <Search size={18} /> RAG 搜尋
          </button>
          <button 
            className={`nav-item ${activeTab === 'stats' ? 'active' : ''}`}
            onClick={() => setActiveTab('stats')}
          >
            <BarChart3 size={18} /> 數據分析
          </button>
        </nav>
        <div className="header-actions">
          <a href="https://github.com" target="_blank" rel="noreferrer" className="github-link">
            <Github size={22} />
          </a>
        </div>
      </header>

      <main className="main-content container">
        {activeTab === 'search' ? (
          <div className="search-page fade-in">
            <div className="hero-section">
              <h1>PTT 智慧輿情問答</h1>
              <p>利用 RAG 技術檢索 PTT 文章，並由 AI 為您整理精確答案。</p>
            </div>
            
            <SearchBar onSearch={handleSearch} isLoading={isLoading} />
            
            {error && <div className="error-message">{error}</div>}
            
            {searchResult && !isLoading ? (
              <ResultView result={searchResult} />
            ) : !isLoading && (
              <div className="search-placeholder">
                <Newspaper size={64} color="#e2e8f0" />
                <p>開始您的第一次搜尋，或是查看數據分析報告。</p>
              </div>
            )}
          </div>
        ) : (
          <div className="stats-page fade-in">
            <div className="hero-section">
              <h1>輿情趨勢概覽</h1>
              <p>即時統計 PTT 文章發布狀況與看板分佈比例。</p>
            </div>
            {stats ? (
              <Dashboard stats={stats} />
            ) : (
              <div className="loading-container">
                <div className="spinner"></div>
                <p>正在載入數據...</p>
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>© 2026 PTT LLM Pulse Analyst. Powered by Gemini & LangChain.</p>
      </footer>

      <style>{`
        .app-wrapper { min-height: 100vh; display: flex; flex-direction: column; background: #f8fafc; color: #1e293b; }
        .app-header { 
          height: 70px; 
          background: #fff; 
          border-bottom: 1px solid #e2e8f0; 
          display: flex; 
          align-items: center; 
          padding: 0 2.5rem;
          position: sticky;
          top: 0;
          z-index: 100;
          box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        }
        .app-logo { display: flex; align-items: center; gap: 0.75rem; font-weight: 800; font-size: 1.35rem; color: #3b82f6; cursor: default; }
        .app-nav { margin-left: 3.5rem; display: flex; gap: 0.5rem; flex: 1; }
        .nav-item { 
          background: transparent; 
          border: none;
          color: #64748b; 
          padding: 0.6rem 1.1rem; 
          font-weight: 600; 
          display: flex; 
          align-items: center; 
          gap: 0.5rem; 
          border-radius: 10px;
          cursor: pointer;
          transition: all 0.2s;
          font-family: inherit;
          font-size: 0.95rem;
        }
        .nav-item:hover { color: #3b82f6; background: #f0f7ff; }
        .nav-item.active { color: #3b82f6; background: #eff6ff; }
        .header-actions { display: flex; align-items: center; }
        .github-link { color: #94a3b8; transition: color 0.2s; }
        .github-link:hover { color: #1e293b; }
        .container { max-width: 1100px; margin: 0 auto; padding: 0 2rem; width: 100%; box-sizing: border-box; }
        .main-content { padding-top: 3rem; padding-bottom: 5rem; }
        .hero-section { text-align: center; margin-bottom: 3.5rem; }
        .hero-section h1 { font-size: 2.75rem; font-weight: 850; margin-bottom: 1rem; color: #0f172a; letter-spacing: -0.03em; }
        .hero-section p { font-size: 1.15rem; color: #64748b; max-width: 600px; margin: 0 auto; line-height: 1.6; }
        .search-placeholder { text-align: center; padding: 6rem 0; color: #cbd5e1; display: flex; flex-direction: column; align-items: center; gap: 1.5rem; }
        .error-message { background: #fef2f2; color: #dc2626; padding: 1.25rem; border-radius: 12px; text-align: center; margin-top: 2rem; border: 1px solid #fee2e2; font-weight: 500; }
        .app-footer { margin-top: auto; padding: 3rem; text-align: center; border-top: 1px solid #e2e8f0; color: #94a3b8; font-size: 0.9rem; background: #fff; }
        .fade-in { animation: fadeIn 0.5s ease-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .loading-container { text-align: center; padding: 6rem; color: #64748b; display: flex; flex-direction: column; align-items: center; gap: 1.25rem; }
        .spinner { width: 44px; height: 44px; border: 4px solid #f1f5f9; border-left-color: #3b82f6; border-radius: 50%; animation: spin 0.8s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}

export default App;
