import axios from 'axios';
// 關鍵：使用 type 關鍵字匯入
import type { SearchResponse, StatisticsResponse } from '../types';

const api = axios.create({
  baseURL: '/api',
});

export const searchArticles = async (question: string, top_k: number = 3): Promise<SearchResponse> => {
  const response = await api.post('/search/', { question, top_k });
  return response.data;
};

export const getStatistics = async (): Promise<StatisticsResponse> => {
  const response = await api.get('/statistics/');
  return response.data;
};

export default api;
