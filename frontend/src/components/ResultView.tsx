import React from 'react';
import Markdown from 'react-markdown';
import type { SearchResponse, Article } from '../types';
import { ExternalLink, User, Calendar, MessageSquare } from 'lucide-react';

interface ResultViewProps {
  result: SearchResponse;
}

const ArticleCard: React.FC<{ article: Article }> = ({ article }) => (
  <div className="article-source-card">
    <div className="article-source-header">
      <span className="article-source-board">[{article.board || 'PTT'}]</span>
      <a href={article.url} target="_blank" rel="noopener noreferrer" className="article-source-link">
        <ExternalLink size={14} />
      </a>
    </div>
    <h4 className="article-source-title">{article.title || '無標題'}</h4>
    <div className="article-source-meta">
      <span className="article-source-author"><User size={12} /> {article.author || '匿名'}</span>
      <span className="article-source-date"><Calendar size={12} /> {article.post_time ? new Date(article.post_time).toLocaleDateString() : '未知'}</span>
    </div>
    <p className="article-source-excerpt">{article.content ? article.content.slice(0, 100) : ''}...</p>
    <style>{`
      .article-source-card { 
        background: #fff; 
        border: 1px solid #e2e8f0; 
        border-radius: 12px; 
        padding: 1rem; 
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
      }
      .article-source-header { display: flex; justify-content: space-between; }
      .article-source-board { color: #3b82f6; font-weight: bold; font-size: 0.75rem; }
      .article-source-title { font-weight: 600; margin: 0.5rem 0; color: #1e293b; font-size: 0.95rem; }
      .article-source-meta { display: flex; gap: 0.75rem; color: #64748b; font-size: 0.7rem; align-items: center; }
      .article-source-excerpt { font-size: 0.85rem; color: #475569; line-height: 1.5; margin-top: 0.5rem; }
    `}</style>
  </div>
);

const ResultView: React.FC<ResultViewProps> = ({ result }) => {
  if (!result || !result.answer) return null;

  return (
    <div className="result-view-container">
      <div className="answer-section">
        <h3 style={{ marginBottom: '1.25rem', color: '#1e293b', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <MessageSquare size={20} color="#3b82f6" /> AI 深度分析
        </h3>
        <div className="markdown-body">
          <Markdown>{result.answer}</Markdown>
        </div>
      </div>
      
      <div className="sources-section">
        <h3 style={{ marginBottom: '1rem', fontSize: '1rem', color: '#1e293b', fontWeight: 'bold' }}>
          參考來源 ({result.related_articles?.length || 0})
        </h3>
        <div className="sources-grid">
          {result.related_articles?.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      </div>

      <style>{`
        .result-view-container { display: grid; grid-template-columns: 1fr 320px; gap: 2rem; margin-top: 2rem; }
        @media (max-width: 900px) { .result-view-container { grid-template-columns: 1fr; } }
        .answer-section { 
          background: #fff; 
          padding: 2rem; 
          border-radius: 16px; 
          border: 1px solid #e2e8f0;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .markdown-body { line-height: 1.8; color: #334155; font-size: 1.05rem; }
        .markdown-body p { margin-bottom: 1.25rem; }
        .markdown-body ul, .markdown-body ol { margin-bottom: 1.25rem; padding-left: 1.5rem; }
        .markdown-body li { margin-bottom: 0.5rem; }
        .markdown-body strong { color: #1e293b; font-weight: 700; }
        .sources-grid { display: flex; flex-direction: column; gap: 0.5rem; }
      `}</style>
    </div>
  );
};

export default ResultView;
