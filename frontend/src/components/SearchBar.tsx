import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

interface SearchBarProps {
  onSearch: (question: string) => void;
  isLoading: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch, isLoading }) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim() && !isLoading) {
      onSearch(question);
    }
  };

  return (
    <div className="search-bar-container">
      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-input-wrapper">
          <Search className="search-icon" size={20} />
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="詢問 PTT 輿情問題... (例如：最近大家對輝達看法如何？)"
            className="search-input"
            disabled={isLoading}
          />
          <button type="submit" className="search-button" disabled={isLoading}>
            {isLoading ? <Loader2 className="animate-spin" size={20} /> : '搜尋'}
          </button>
        </div>
      </form>
      <style>{`
        .search-bar-container {
          width: 100%;
          max-width: 800px;
          margin: 2rem auto;
        }
        .search-form {
          width: 100%;
        }
        .search-input-wrapper {
          display: flex;
          align-items: center;
          background: var(--bg-card);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          padding: 0.5rem 1rem;
          box-shadow: var(--shadow);
          transition: all 0.2s;
        }
        .search-input-wrapper:focus-within {
          border-color: var(--primary);
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        .search-icon {
          color: var(--text-muted);
          margin-right: 0.75rem;
        }
        .search-input {
          flex: 1;
          border: none;
          outline: none;
          padding: 0.75rem 0;
          font-size: 1rem;
          background: transparent;
        }
        .search-button {
          background: var(--primary);
          color: white;
          padding: 0.6rem 1.25rem;
          font-weight: 600;
          margin-left: 0.5rem;
        }
        .search-button:hover:not(:disabled) {
          background: var(--primary-hover);
        }
        .search-button:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }
        .animate-spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default SearchBar;
