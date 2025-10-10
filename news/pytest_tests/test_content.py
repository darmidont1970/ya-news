import pytest
from pytest_lazy_fixtures import lf

from datetime import datetime, timedelta
from http import HTTPStatus
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from news.models import Comment, News
from news.forms import CommentForm


@pytest.fixture
def home_page_news():
    """We create the required number of news items for testing."""
    today = datetime.today()
    News.objects.bulk_create(
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    )


def test_home_page_news_count(home_page_news, client):
    """
    The home page displays no more than NEWS_COUNT_ON_HOME_PAGE news items.
    """
    response = client.get(reverse('news:home'))
    assert response.status_code == HTTPStatus.OK
    object_list = response.context['object_list']
    assert object_list.count() == settings.NEWS_COUNT_ON_HOME_PAGE


def test_home_page_news_order(home_page_news, client):
    """News on the main page is sorted by date (newest first)."""
    response = client.get(reverse('news:home'))
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.fixture
def detail_page_data(news, author):
    """We create comments for the news."""
    now = timezone.now()
    comments = []
    for index in range(10):
        comments.append(Comment(
            news=news,
            author=author,
            text=f'Комментарий {index}',
            created=now + timedelta(days=index)
        ))
    Comment.objects.bulk_create(comments)


def test_detail_page_comments_order(detail_page_data, client, id_for_news):
    """Comments to the news are sorted by ascending creation date."""
    response = client.get(reverse('news:detail', args=id_for_news))
    news = response.context['news']
    all_comments = news.comment_set.all()
    timestamps = [c.created for c in all_comments]
    assert timestamps == sorted(timestamps)


@pytest.mark.parametrize(
    'parametrized_client, is_form',
    (
        (lf('author_client'), True),
        (lf('reader_client'), True),
        (lf('client'), False),
    )
)
def test_detail_pages_contains_form(parametrized_client, is_form, id_for_news):
    url = reverse('news:detail', args=id_for_news)
    response = parametrized_client.get(url)
    assert ('form' in response.context) == is_form
    if is_form:
        assert isinstance(response.context['form'], CommentForm)
