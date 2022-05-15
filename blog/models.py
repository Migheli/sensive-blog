from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count


class PostQuerySet(models.QuerySet):

    def year(self, year):
        posts_at_year = self.filter(published_at__year=year).order_by('published_at')
        return posts_at_year

    def popular(self):
        posts = self.annotate(num_likes=Count('likes'))
        tags_by_popularity = posts.order_by('-num_likes')
        return tags_by_popularity

    def fetch_with_comments_count(self):

        '''
        Функция позволяет оптимизировать запросы, чтобы избежать использования 2 annotate.
        Использование 2 annotate нежелательно из-за поглощения большого количества ресурсов.
        В данной функции добавление полей num_comments происходит на уровне Python без обращения к БД,
        что сокращает количество запросов к БД и, соответственно, время исполнения.
        '''

        related_posts_id = [post.id for post in self]
        posts_with_comments = Post.objects.filter(id__in=related_posts_id).annotate(num_comments=Count('comments'))
        ids_and_comments = posts_with_comments.values_list('id', 'num_comments')
        count_for_id = dict(ids_and_comments)

        for post in self:
            post.num_comments = count_for_id[post.id]

        return self


class Post(models.Model):

    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True})

    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)

    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})


class TagQuerySet(models.QuerySet):

    def popular(self):
        tags = self.annotate(num_posts=Count('posts'))
        tags_by_popularity = tags.order_by('-num_posts')
        return tags_by_popularity


class Tag(models.Model):

    title = models.CharField('Тег', max_length=20, unique=True)
    objects = TagQuerySet.as_manager()

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    def clean(self):
        self.title = self.title.lower()


class Comment(models.Model):

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        verbose_name='Пост, к которому написан',
        related_name='comments')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'
