from django.urls import path
from . import views

urlpatterns = [
    # 設定 /api/posts/ 對應到 ArticleListView
    path('posts/', views.ArticleListView.as_view(), name='article-list'),
]