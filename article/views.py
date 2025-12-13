from datetime import datetime, time
import traceback

from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import LimitOffsetPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, inline_serializer

from .models import Article
from .serializers import ArticleSerializer, ArticleListRequestSerializer, QueryRequestSerializer
from .rag_query import run_rag_query
from log_app.models import Log

# --- 提取出來的共用篩選邏輯 ---
def articles_filter(article_list_request_serializer):
    # 取得初始 QuerySet
    articles = Article.objects.all()
    
    # 取得驗證後的參數
    validated_data = article_list_request_serializer.validated_data
    author_name = validated_data.get("author_name")
    board_name = validated_data.get("board_name")
    start_date = validated_data.get("start_date")
    end_date = validated_data.get("end_date")
    
    # 進行篩選 (修正：使用 author 而非 author__name，因為您的模型是 CharField)
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
        
    return articles

# --- 1. 文章列表 API ---
class ArticleListView(APIView):
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
        # 1. 驗證參數
        request_serializer = ArticleListRequestSerializer(data=request.query_params)
        if not request_serializer.is_valid():
            Log.objects.create(level='ERROR', category='user-posts', message='查詢參數不合法',
                               traceback=traceback.format_exc())
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. 使用共用函式進行篩選
        articles = articles_filter(request_serializer)
        
        # 3. 分頁處理 (加上 order_by 確保排序穩定)
        paginator = LimitOffsetPagination()
        paginator.default_limit = 50
        paginated_queryset = paginator.paginate_queryset(articles.order_by('-post_time'), request)
        
        # 4. 回傳結果
        serializer = ArticleSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

# --- 2. 單篇文章詳情 API (新增) ---
class ArticleDetailView(APIView):
    @extend_schema(
        description="根據文章 ID 取得特定文章的詳細內容。",
        responses={
            200: ArticleSerializer(),
            404: OpenApiResponse(response={"type": "object", "properties": {"error": {"type": "string"}}})
        }
    )
    def get(self, request, pk):
        # 防呆檢查
        if pk <= 0:
            error_msg = "文章ID須為正數"
            Log.objects.create(level='ERROR', category='user-posts_id', message=error_msg)
            return Response({"error": error_msg}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            article = Article.objects.get(id=pk)
        except Article.DoesNotExist:
            error_msg = "找不到文章，請輸入正確文章ID"
            Log.objects.create(level='ERROR', category='user-posts_id', message=error_msg, traceback=traceback.format_exc())
            return Response({"error": error_msg}, status=status.HTTP_404_NOT_FOUND)
            
        return Response(ArticleSerializer(article).data, status=status.HTTP_200_OK)

# --- 3. 文章統計 API (新增) ---
class ArticleStatisticsView(APIView):
    @extend_schema(
        description="取得文章統計資訊，支援時間範圍、作者名稱和版面過濾",
        parameters=[
            OpenApiParameter("author_name", str, OpenApiParameter.QUERY, description="篩選特定發文者的文章"),
            OpenApiParameter("board_name", str, OpenApiParameter.QUERY, description="篩選特定版面的文章"),
            OpenApiParameter("start_date", str, OpenApiParameter.QUERY, description="篩選起始日期 (YYYY-MM-DD)"),
            OpenApiParameter("end_date", str, OpenApiParameter.QUERY, description="篩選結束日期 (YYYY-MM-DD)"),
        ],
        responses={
            200: OpenApiResponse(response={"type": "object", "properties": {"total_articles": {"type": "integer"}}}),
            400: OpenApiResponse(response={"type": "object", "properties": {"error": {"type": "string"}}}),
        }
    )
    def get(self, request):
        request_serializer = ArticleListRequestSerializer(data=request.query_params)
        
        if not request_serializer.is_valid():
            Log.objects.create(level='ERROR', category='user-posts-stats', message='查詢參數不合法')
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        # 複用篩選邏輯，但這次我們只需要 count()
        articles = articles_filter(request_serializer)
        total_articles = articles.count()
        
        return Response({"total_articles": total_articles})
    
# [新增] 搜尋 API View
class SearchAPIView(APIView):
    @extend_schema(
        methods=["POST"],
        summary="AI 語意搜尋",
        description="輸入問題 (question) 與檢索數量 (top_k)，系統會透過 RAG 流程搜尋相關文章並由 Gemini 生成回答。",
        request=QueryRequestSerializer,
        responses={200: QueryRequestSerializer}
    )
    def post(self, request):
        # 1. 驗證輸入參數
        serializer = QueryRequestSerializer(data=request.data)
        if not serializer.is_valid():
            Log.objects.create(level='ERROR', category='user-search', message='查詢參數不合法')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        question = serializer.validated_data.get("question")
        top_k = serializer.validated_data.get("top_k")
        
        # 2. 呼叫我們封裝好的 RAG 服務
        result = run_rag_query(question, top_k)
        
        # 3. 處理錯誤
        if "error" in result:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        # 4. 回傳結果
        # 使用 Serializer 進行輸出格式化
        response_serializer = QueryRequestSerializer(instance=result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)