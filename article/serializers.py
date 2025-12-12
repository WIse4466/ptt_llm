from rest_framework import serializers
from .models import Article

# 1. 文章資料序列化 (負責將資料庫內容轉成 JSON 回傳給前端)
class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'

# 2. 查詢參數序列化 (負責驗證 GET 請求的參數，如 author_name, start_date 等)
class ArticleListRequestSerializer(serializers.Serializer):
    author_name = serializers.CharField(help_text="作者名稱", write_only=True, required=False)
    board_name = serializers.CharField(help_text="看板名稱", write_only=True, required=False)
    start_date = serializers.DateField(help_text="起始日期", write_only=True, required=False)
    end_date = serializers.DateField(help_text="結束日期", write_only=True, required=False)
    limit = serializers.IntegerField(help_text="每頁返回的筆數 (預設 50)", write_only=True, default=50, min_value=1)
    offset = serializers.IntegerField(help_text="從第幾筆開始 (預設 0)", write_only=True, required=False, min_value=0)