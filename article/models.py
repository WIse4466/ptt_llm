from django.db import models

# Create your models here.
class Article(models.Model):
    board = models.CharField(max_length=100) # 看板名稱
    title = models.CharField(max_length=255) # 文章標題
    author = models.CharField(max_length=100) # 作者帳號
    content = models.TextField() # 文章內文
    post_time = models.DateTimeField() # po文時間
    url = models.URLField(max_length=255) # 文章連結

    def __str__(self):
        return f"[{self.board}] {self.title}"
    
class Comment(models.Model):
    # ForeignKey 連結到 Article，當文章被刪除時，推文也會一起刪除 (CASCADE)
    # related_name='comments' 讓我們可以用 article.comments.all() 取得該文章所有推文
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')

    tag = models.CharField(max_length=10)           # 推、噓、箭頭
    user_id = models.CharField(max_length=100)      # 推文者 ID
    content = models.TextField()                    # 推文內容
    ip_datetime = models.CharField(max_length=100)  # 推文時間/IP

    def __str__(self):
        return f"{self.tag} {self.user_id}: {self.content}"