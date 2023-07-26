from django.urls import path, re_path
from . import views
from .feeds import LastestPostsFeed

app_name = 'blog'

urlpatterns = [
    # post views
    # path('', views.PostListView.as_view(), name='post_list'),
    path('', views.post_list, name='post_list'),
    path('tag/<slug:tag_slug>/', views.post_list, name='post_list_by_tag'),

    # path('<int:id>/', views.post_detail, name='post_detail'),
    # 정규표현식으로 변경하여 서치하는 과정을 개선
    # path('<int:year>/<int:month>/<int:day>/<str:post>', views.post_detail, name='post_detail'),
    re_path(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/(?P<post>[-\w]+)/$', views.post_detail,
            name='post_detail'),
    path('<int:post_id>/share/', views.post_share, name='post_share'),
    path('<int:post_id>/comment/', views.post_comment, name='post_comment'),
    path('feed/', LastestPostsFeed(), name='post_feed'),
    path('search/', views.post_search, name='post_search'),
]
