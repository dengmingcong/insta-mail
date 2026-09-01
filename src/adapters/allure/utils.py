from urllib.parse import urlparse


def get_url_path(url: str) -> str:
    """Extract path from url.

    >>> get_url_path("foo")
    'foo'
    >>> get_url_path("http://bar.com/baz")
    '/baz'
    """
    if "/" not in url:
        return url

    return urlparse(url).path
