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