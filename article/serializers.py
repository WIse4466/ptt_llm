from rest_framework import serializers
from .models import Article, Comment

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        # 只顯示我們感興趣的欄位
        fields = ['tag', 'user_id', 'content', 'ip_datetime']

# 1. 文章資料序列化 (負責將資料庫內容轉成 JSON 回傳給前端)
class ArticleSerializer(serializers.ModelSerializer):
    # 【關鍵修改】顯式宣告 comments 欄位
    # many=True: 因為一篇文章有多則推文
    # read_only=True: 我們只讀取，不透過這個 API 修改推文
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        # 雖然寫了 __all__，但加上面的宣告後，comments 就會被包含進去了
        fields = ['id', 'board', 'title', 'author', 'post_time', 'url', 'content', 'comments']

# 2. 查詢參數序列化 (負責驗證 GET 請求的參數，如 author_name, start_date 等)
class ArticleListRequestSerializer(serializers.Serializer):
    author_name = serializers.CharField(help_text="作者名稱", write_only=True, required=False)
    board_name = serializers.CharField(help_text="看板名稱", write_only=True, required=False)
    start_date = serializers.DateField(help_text="起始日期", write_only=True, required=False)
    end_date = serializers.DateField(help_text="結束日期", write_only=True, required=False)
    limit = serializers.IntegerField(help_text="每頁返回的筆數 (預設 50)", write_only=True, default=50, min_value=1)
    offset = serializers.IntegerField(help_text="從第幾筆開始 (預設 0)", write_only=True, required=False, min_value=0)

# --- [新增] RAG 搜尋用的 Serializer ---
class QueryRequestSerializer(serializers.Serializer):
    # 輸入欄位
    question = serializers.CharField(help_text="查詢內容", required=True, max_length=100, min_length=1)
    top_k = serializers.IntegerField(
        help_text="控制查詢的文章片段數量 (預設 3)", 
        default=3, 
        write_only=True, 
        min_value=1, 
        max_value=10
    )

    # 輸出欄位 (唯讀)
    answer = serializers.CharField(required=False, read_only=True)
    # 這裡重用 ArticleSerializer 來格式化相關文章
    related_articles = ArticleSerializer(many=True, read_only=True)