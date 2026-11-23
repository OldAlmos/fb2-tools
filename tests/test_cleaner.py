import pytest

from fb2tools.cleaner import delete_files, iter_bak_files


@pytest.fixture
def folder_with_bak(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.fb2.bak").write_bytes(b"1")
    (tmp_path / "sub" / "B.FB2.bak").write_bytes(b"2")
    (tmp_path / "book.fb2").write_bytes(b"3")      # обычная книга, трогать нельзя
    (tmp_path / "other.bak").write_bytes(b"4")     # чужой .bak, трогать нельзя
    return tmp_path


def test_iter_bak_files_finds_only_fb2_bak(folder_with_bak):
    found = {p.name for p in iter_bak_files(folder_with_bak)}
    assert found == {"a.fb2.bak", "B.FB2.bak"}


def test_delete_files_removes_them(folder_with_bak):
    files = list(iter_bak_files(folder_with_bak))
    deleted, failed = delete_files(files)
    assert len(deleted) == 2 and failed == []
    assert not (folder_with_bak / "a.fb2.bak").exists()
    assert (folder_with_bak / "book.fb2").exists()
    assert (folder_with_bak / "other.bak").exists()
