from http import HTTPStatus
import pytest
from pytest_django.asserts import assertRedirects
from django.urls import reverse

from news.models import Comment
from news.forms import BAD_WORDS, WARNING


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, id_for_news, form_data):
    """An anonymous user cannot create a comment."""
    url = reverse('news:detail', args=id_for_news)
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    assertRedirects(response, expected_url)
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_authorized_user_can_create_comment(
    author_client, author,
    id_for_news,
    form_data
):
    """An authorized user can create a comment."""
    url = reverse('news:detail', args=id_for_news)
    response = author_client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f'{url}#comments'
    assert Comment.objects.count() == 1
    comment = Comment.objects.get()
    assert comment.text == form_data['text']
    assert comment.news.id == id_for_news[0]
    assert comment.author == author


@pytest.mark.django_db
def test_user_cant_use_bad_words(author_client, id_for_news):
    """
    A comment with a stop word is not created;
    a form error is displayed.
    """
    bad_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    url = reverse('news:detail', args=id_for_news)
    response = author_client.post(url, data=bad_data)
    form = response.context['form']
    assert form.errors['text'] == [WARNING]
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_author_can_delete_comment(author_client, id_for_comment):
    """The author of the comment can delete their comment."""
    url_to_comments = reverse('news:detail', args=id_for_comment) + '#comments'
    delete_url = reverse('news:delete', args=id_for_comment)
    response = author_client.delete(delete_url)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == url_to_comments
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_reader_cant_delete_comment(reader_client, id_for_comment):
    """A user cannot delete someone else's comment."""
    delete_url = reverse('news:delete', args=id_for_comment)
    response = reader_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1


@pytest.mark.django_db
def test_author_can_edit_comment(author_client, comment, form_data):
    """The author of the comment can edit it."""
    url_to_comments = reverse('news:detail', args=(comment.id,)) + '#comments'
    edit_url = reverse('news:edit', args=(comment.id,))
    response = author_client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == url_to_comments
    comment.refresh_from_db()
    assert comment.text == form_data['text']


@pytest.mark.django_db
def test_reader_cant_edit_comment(reader_client, comment, form_data):
    """The user cannot edit someone else's comment."""
    edit_url = reverse('news:edit', args=(comment.id,))
    response = reader_client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment.news == comment_from_db.news
    assert comment.author == comment_from_db.author
    assert comment.text == comment_from_db.text
    assert comment.created == comment_from_db.created
