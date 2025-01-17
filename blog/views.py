from django.shortcuts import render
from django.db.models import Count
from blog.models import Post, Tag
from django.db.models import Prefetch


def serialize_post(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.num_comments,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.num_posts,
    }


def index(request):
    prefetch = Prefetch('tags', queryset=Tag.objects.annotate(num_posts=Count('posts')))
    posts_prepared = Post.objects.prefetch_related(prefetch).select_related('author')
    most_popular_posts = posts_prepared.popular()[:5].fetch_with_comments_count()
    most_fresh_posts = posts_prepared[:5].fetch_with_comments_count()
    most_popular_tags = Tag.objects.popular()

    context = {

        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
        'page_posts': [serialize_post(post) for post in most_fresh_posts],

        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],

    }
    return render(request, 'index.html', context)


def post_detail(request, slug):

    prefetched_tags = Prefetch('tags', queryset=Tag.objects.annotate(num_posts=Count('posts')))
    posts_selected_by_authors = Post.objects.select_related('author')
    posts_prepared = posts_selected_by_authors.prefetch_related(prefetched_tags).annotate(num_likes=Count('likes'))
    post = posts_prepared.get(slug=slug)
    comments = post.comments.select_related('author')

    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': post.num_likes,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
    }

    most_popular_tags = Tag.objects.popular()
    most_popular_posts = posts_prepared.popular()[:5].select_related('author').fetch_with_comments_count()

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):

    tag = Tag.objects.get(title=tag_title)
    prefetched_tags = Prefetch('tags', queryset=Tag.objects.annotate(num_posts=Count('posts')))
    posts_selected_by_authors = Post.objects.select_related('author')
    posts_prepared = posts_selected_by_authors.prefetch_related(prefetched_tags).annotate(num_likes=Count('likes'))
    most_popular_posts = posts_prepared.popular()[:5].fetch_with_comments_count()
    related_posts_with_selected_authors = tag.posts.all()[:20].select_related('author')
    related_posts = related_posts_with_selected_authors.prefetch_related(prefetched_tags).fetch_with_comments_count()
    most_popular_tags = Tag.objects.popular()[:5]

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
