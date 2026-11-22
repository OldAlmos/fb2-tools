import pytest

NS_ATTRS = (
    'xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" '
    'xmlns:l="http://www.w3.org/1999/xlink"'
)


def make_fb2(body: str = "<section><p>Текст</p></section>", extra: str = "") -> bytes:
    """Собирает корректный FB2. extra вставляется после </body> (например, <binary>)."""
    text = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f"<FictionBook {NS_ATTRS}>\n"
        "<description><title-info><book-title>Тест</book-title></title-info></description>\n"
        f"<body>{body}</body>\n"
        f"{extra}\n"
        "</FictionBook>\n"
    )
    return text.encode("utf-8")


@pytest.fixture
def good_fb2() -> bytes:
    return make_fb2()


@pytest.fixture
def fb2_factory():
    return make_fb2
