from datetime import datetime, time
from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import LimitOffsetPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, inline_serializer
from .models import Article
from .serializers import ArticleSerializer, ArticleListRequestSerializer
import traceback
from log_app.models import Log

class ArticleListView(APIView):
    # API 文件描述 (讓 Swagger UI 顯示漂亮的說明)
    @extend_schema(
        description="取得最新 50 篇文章，可使用 limit、offset 進行分頁，可使用作者名稱、版面、時間範圍進行過濾。",
        parameters=[
            OpenApiParameter("limit", int, OpenApiParameter.QUERY, description="每頁返回的筆數 (預設 50)"),
            OpenApiParameter("offset", int, OpenApiParameter.QUERY, description="從第幾筆開始 (預設 0)"),
            OpenApiParameter("author_name", str, OpenApiParameter.QUERY, description="篩選特定發文者的文章"),
            OpenApiParameter("board_name", str, OpenApiParameter.QUERY, description="篩選特定版面的文章"),
            OpenApiParameter("start_date", str, OpenApiParameter.QUERY, description="篩選起始日期 (YYYY-MM-DD)"),
            OpenApiParameter("end_date", str, OpenApiParameter.QUERY, description="篩選結束日期 (YYYY-MM-DD)"),
        ],
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='ArticleListResponse',
                    fields={
                        'count': serializers.IntegerField(read_only=True),
                        'next': serializers.CharField(read_only=True),
                        'previous': serializers.CharField(read_only=True),
                        'results': ArticleSerializer(many=True, read_only=True),
                    }
                ),
            )
        },
    )
    def get(self, request):
        # 1. 驗證輸入參數
        request_serializer = ArticleListRequestSerializer(data=request.query_params)
        if not request_serializer.is_valid():
            # 參數錯誤：寫入 Log 並回傳 400
            Log.objects.create(level='ERROR', category='user-posts', message='查詢參數不合法',
                               traceback=traceback.format_exc())
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. 準備查詢集 (QuerySet)
        articles = Article.objects.all()
        
        # 3. 取得驗證後的參數
        validated_data = request_serializer.validated_data
        author_name = validated_data.get("author_name")
        board_name = validated_data.get("board_name")
        start_date = validated_data.get("start_date")
        end_date = validated_data.get("end_date")
        
        # 4. 進行篩選邏輯
        if author_name:
            articles = articles.filter(author=author_name)
        if board_name:
            articles = articles.filter(board=board_name)
        
        # 時間範圍處理
        start_datetime = datetime.combine(start_date, time.min) if start_date else None
        end_datetime = datetime.combine(end_date, time.max) if end_date else None
        
        if start_datetime and end_datetime:
            articles = articles.filter(post_time__range=[start_datetime, end_datetime])
        elif start_datetime:
            articles = articles.filter(post_time__gte=start_datetime)
        elif end_datetime:
            articles = articles.filter(post_time__lte=end_datetime)
            
        # 5. 分頁處理 (加上 order_by 確保排序穩定)
        paginator = LimitOffsetPagination()
        paginator.default_limit = 50
        paginated_queryset = paginator.paginate_queryset(articles.order_by('-post_time'), request)
        
        # 6. 回傳結果
        serializer = ArticleSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)