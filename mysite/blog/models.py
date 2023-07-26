from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from taggit.managers import TaggableManager


# Create your models here

class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)


class Post(models.Model):
    class Status(models.TextChoices):  # 열거형 클래스
        DRAFT = 'DF', 'Draft'  # 임시
        PUBLISHED = 'PB', 'Published'  # 게시 됨

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique_for_date='publish', allow_unicode=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blog_posts'  # User 에서 Post 로의 반대 관계의 이름을 지정
    )
    body = models.TextField()
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.DRAFT
    )
    objects = models.Manager()  # 기본 매니저
    published = PublishedManager()  # 사용자 정의 매니저
    tags = TaggableManager()

    class Meta:
        ordering = ['-publish']  # 오름차순은 시간 순, - 가 붙었으니 역순 = 가장 최신 -> 맨 위
        indexes = [
            models.Index(fields=['-publish']),
        ]

    def get_absolute_url(self):
        # return reverse('blog:post_detail', args=[self.id])
        return reverse('blog:post_detail',
                       args=[self.publish.year,
                             self.publish.month,
                             self.publish.day,
                             self.slug])

    # reverse 매치에서 그냥 str 로 받게 되면 오동작 발생 가능성이 있기 때문에
    # 성능면에서도 개선 가능한 정규표현식으로 넣어두는게 좋다.
    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='comments')
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created']
        indexes = [
            models.Index(fields=['created']),
        ]

    def __str__(self):
        return f'Comment by {self.name} on {self.post}'
