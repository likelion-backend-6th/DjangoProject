from django.shortcuts import render
from .models import Post, Comment
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm, SearchForm
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity


# Create your views here.
class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])

    # 페이지당 3개의 게시물로 페이지네이션
    paginator = Paginator(post_list, 3)
    # 페이지를 찾아서 들어가는 과정에서 에러처리
    page_number = request.GET.get('page', 1)

    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    # posts = paginator.page(page_number)
    return render(request, 'blog/post/list.html', {'posts': posts, 'tag': tag})


def post_detail(request, year, month, day, post):
    # try:
    #     post = Post.published.get(id=id)
    #
    # except Post.DoesNotExist:
    #     raise Http404("No Post Found.")

    # 내장 함수를 이용해서 간략히 404를 정리
    post = get_object_or_404(Post,
                             status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    # List of active comments for this post
    comments = post.comments.filter(active=True)
    # Form for users to comment
    form = CommentForm()
    # List of similar posts
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    # annotate 를 이용하여 필드를 추가하는
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    return render(request, 'blog/post/detail.html',
                  {'post': post, 'comments': comments, 'form': form, 'similar_posts': similar_posts})


def post_share(request, post_id):
    # search post by id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':
        # form sent
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # if form field is valid
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} 님이 {post.title}을(를) 추천합니다."
            message = f"{post.title}을(를) {post_url} 에서 읽어보세요.\n\n" \
                      f"{cd['name']}의 의견: {cd['comments']}"
            send_mail(subject, message, 'ivankimmh@gmail.com', [cd["to"]])
            # ... sending email ...
            sent = True
    else:
        form = EmailPostForm()

    return render(request, 'blog/post/share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    # A comment was posted
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Create a Commnet obejct without saving it to the database
        comment = form.save(commit=False)
        # Assign the post to the comment
        comment.post = post
        # Save the comment to the database
        comment.save()
    return render(request, 'blog/post/comment.html', {'post': post, 'form': form, 'comment': comment})


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:  # form 이 제출됐는지 확인
        form = SearchForm(request.GET)
        # if form.is_valid():
        #     query = form.cleaned_data['query']
        #     results = Post.published.annotate(
        #         search=SearchVector('title', 'body'), ).filter(search__contains=query)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B')
            search_query = SearchQuery(query)
            results = Post.published.annotate(
                similarity=TrigramSimilarity('title', query),
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
            ).filter(similarity__gt=0.1).order_by('-similarity')
    return render(request, 'blog/post/search.html', {'form': form, 'query': query, 'results': results})
