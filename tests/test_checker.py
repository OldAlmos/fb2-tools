import zipfile

from fb2tools.checker import check_bytes, check_file, iter_fb2_files


def test_good_file_has_no_errors(good_fb2):
    assert check_bytes(good_fb2) == []


def test_broken_xml():
    errors = check_bytes(b"<FictionBook><description>")
    assert len(errors) == 1
    assert "XML не разбирается" in errors[0]


def test_wrong_root_element():
    errors = check_bytes(b"<html><body/></html>")
    assert errors and "неверный корневой элемент" in errors[0]


def test_missing_body():
    data = (
        b'<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">'
        b"<description><title-info><book-title>T</book-title></title-info></description>"
        b"</FictionBook>"
    )
    assert "нет <body>" in check_bytes(data)


def test_image_without_binary(fb2_factory):
    body = '<section><image l:href="#pic1"/></section>'
    errors = check_bytes(fb2_factory(body=body))
    assert any("#pic1" in e for e in errors)


def test_image_with_binary_is_ok(fb2_factory):
    body = '<section><image l:href="#pic1"/></section>'
    extra = '<binary id="pic1" content-type="image/png">AAAA</binary>'
    assert check_bytes(fb2_factory(body=body, extra=extra)) == []


def test_check_file_plain_fb2(tmp_path, good_fb2):
    path = tmp_path / "book.fb2"
    path.write_bytes(good_fb2)
    assert check_file(path) == []


def test_check_file_zip(tmp_path, good_fb2):
    path = tmp_path / "book.fb2.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("book.fb2", good_fb2)
    assert check_file(path) == []


def test_check_file_zip_without_fb2(tmp_path):
    path = tmp_path / "empty.fb2.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("readme.txt", "нет книги")
    assert check_file(path) == ["в архиве нет .fb2"]


def test_iter_fb2_files_recursive_and_case_insensitive(tmp_path, good_fb2):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.fb2").write_bytes(good_fb2)
    (tmp_path / "sub" / "B.FB2").write_bytes(good_fb2)
    # (tmp_path / "notes.txt").write_text("не книга")
    (tmp_path / "notes.txt").write_text("не книга", encoding="utf-8")
    found = {p.name for p in iter_fb2_files(tmp_path)}
    assert found == {"a.fb2", "B.FB2"}
