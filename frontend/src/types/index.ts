// 定義文章結構
export type Article = {
  id: number;
  board: string;
  title: string;
  author: string;
  post_time: string;
  url: string;
  content: string;
  comments?: Comment[];
}

// 定義留言結構
export type Comment = {
  tag: string;
  user_id: string;
  content: string;
  ip_datetime: string;
}

// 搜尋結果
export type SearchResponse = {
  answer: string;
  related_articles: Article[];
}

// 統計數據
export type StatisticsResponse = {
  total_articles: number;
  board_distribution: { board: string; count: number }[];
  daily_counts: { date: string; count: number }[];
}

// 強迫 Vite 識別為 JS 模組
export const VERSION = '1.0.0';
