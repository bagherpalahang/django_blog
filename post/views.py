from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.postgres.search import SearchVector
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.db.models import Count
from django.core.mail import send_mail

from blog import settings  
from taggit.models import Tag
from .forms import EmailPostForm, CommentForm, SearchForm
from .models import Post
# Create your views here.


class PostListView(ListView):

    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 2
    template_name = 'post/list.html'

def post_list(request, tag_slug=None):
    
    posts = Post.published.all()
    tag = None
    
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts = posts.filter(tags__in=[tag])

    paginator = Paginator(posts, 2)
    page_number = request.GET.get('page', 1)

    try:
        posts = paginator.page(page_number)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        posts = paginator.page(1)

    return render(request, 'post/list.html', {'posts':posts, 'tag':tag})

def post_detail(request, post, year, month, day):
    post = get_object_or_404(Post, status=Post.Status.PUBLISHED, slug=post, publish__year=year, publish__month=month, publish__day=day)
    comments = post.post_comment.filter(active=True)
    form = CommentForm()

    post_tags_id = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_id).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', 'publish')[:4]

    return render(request, 'post/detail.html', {'post':post, 'comments':comments, 'form':form, 'similar_posts':similar_posts})

def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False

    if request.method == "POST":
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recomend\'s you read {post.title}"
            message = f"read {post.title}, at {post_url} \n\n {cd['name']}\'s comments : {cd['comments']}"
            send_mail(subject, message, settings.EMAIL_HOST_USER, [cd['to']])
            sent = True
    else:
        form = EmailPostForm()

    return render(request, 'post/share.html', {'post':post, 'form':form, 'sent': sent})

def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    form = CommentForm(data=request.POST)
    comment = None

    if form.is_valid:
        comment = form.save(commit=False)
        comment.post = post
        comment.save()

    return render(request, 'post/comment.html', {"post":post, "form":form, "comment":comment})

def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            results = Post.published.annotate(search=SearchVector('title', 'body'),).filter(search=query)

    return render(request, 'post/search.html', {'form': form, 'query': query, 'results': results})