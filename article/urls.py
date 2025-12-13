from django.urls import path
from . import views

urlpatterns = [
    # 設定 /api/posts/ 對應到 ArticleListView
    path('posts/', views.ArticleListView.as_view(), name='article-list'),

    # 詳細內容 API
    path('posts/<int:pk>/', views.ArticleDetailView.as_view(), name='article-detail'),
    
    # 統計 API
    path('statistics/', views.ArticleStatisticsView.as_view(), name='article-statistics'),

    # 搜尋 API
    path('search/', views.SearchAPIView.as_view(), name='article-search'),
]