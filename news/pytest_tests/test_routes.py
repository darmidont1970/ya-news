from http import HTTPStatus

import pytest
from pytest_lazy_fixtures import lf
from pytest_django.asserts import assertRedirects
from django.urls import reverse


@pytest.mark.parametrize(
    'name, args',
    (
        ('news:home', None),
        ('news:detail', lf('id_for_news')),
        ('users:login', None),
        ('users:signup', None),
    )
)
def test_pages_availability_for_anonymous_user(client, name, args):
    """Availability of public pages."""
    if args is None:
        url = reverse(name)
    else:
        url = reverse(name, args=args)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_logout_availability_for_anonymous_user(client):
    """We check that the anonymous user can log out and receive a redirect."""
    url = reverse('users:logout')
    response = client.get(url)
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    response = client.post(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    (
        (lf('author_client'), HTTPStatus.OK),
        (lf('reader_client'), HTTPStatus.NOT_FOUND),
    )
)
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete')
)
def test_pages_availability_for_different_users(
    parametrized_client,
    expected_status,
    name,
    id_for_comment
):
    """The author can edit/delete the news, others cannot."""
    url = reverse(name, args=id_for_comment)
    response = parametrized_client.get(url)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete')
)
def test_redirects(client, name, id_for_comment):
    """The anonymous user is redirected to the login page."""
    login_url = reverse('users:login')
    url = reverse(name, args=id_for_comment)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
