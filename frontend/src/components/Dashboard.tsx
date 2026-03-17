import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Pie } from 'react-chartjs-2';
import type { StatisticsResponse } from '../types';

// 明確註冊
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface DashboardProps {
  stats: StatisticsResponse;
}

const Dashboard: React.FC<DashboardProps> = ({ stats }) => {
  if (!stats || !stats.daily_counts || !stats.board_distribution) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>數據載入中...</div>;
  }

  const lineData = {
    labels: stats.daily_counts.map(d => d.date),
    datasets: [
      {
        label: '每日文章數量',
        data: stats.daily_counts.map(d => d.count),
        fill: true,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
      },
    ],
  };

  const pieData = {
    labels: stats.board_distribution.map(d => d.board),
    datasets: [
      {
        data: stats.board_distribution.map(d => d.count),
        backgroundColor: [
          '#3b82f6',
          '#10b981',
          '#f59e0b',
          '#ef4444',
          '#8b5cf6',
          '#ec4899',
        ],
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
    },
  };

  return (
    <div className="dashboard-container">
      <div className="stats-overview">
        <div className="stat-card">
          <span className="stat-label">總文章量</span>
          <span className="stat-value">{stats.total_articles}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">看板數量</span>
          <span className="stat-value">{stats.board_distribution.length}</span>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <h3 className="chart-title">輿情趨勢 (每日發文)</h3>
          <div style={{ height: '300px', position: 'relative' }}>
            <Line data={lineData} options={options} />
          </div>
        </div>
        <div className="chart-card">
          <h3 className="chart-title">看板分佈</h3>
          <div style={{ height: '300px', position: 'relative' }}>
            <Pie data={pieData} options={options} />
          </div>
        </div>
      </div>

      <style>{`
        .dashboard-container { margin-top: 1rem; }
        .stats-overview {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }
        .stat-card {
          background: #fff;
          padding: 1.5rem;
          border-radius: 16px;
          border: 1px solid #e2e8f0;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        .stat-label { font-size: 0.875rem; color: #64748b; margin-bottom: 0.5rem; }
        .stat-value { font-size: 2.5rem; font-weight: 800; color: #3b82f6; }
        .charts-grid {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 1.5rem;
        }
        @media (max-width: 900px) {
          .charts-grid { grid-template-columns: 1fr; }
        }
        .chart-card {
          background: #fff;
          padding: 1.5rem;
          border-radius: 16px;
          border: 1px solid #e2e8f0;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .chart-title { font-size: 1rem; font-weight: 700; margin-bottom: 1.5rem; color: #1e293b; }
      `}</style>
    </div>
  );
};

export default Dashboard;
