import pytest

from fb2tools.cli import main


@pytest.fixture
def folder_with_bak(tmp_path):
    (tmp_path / "a.fb2.bak").write_bytes(b"1")
    (tmp_path / "book.fb2").write_bytes(b"3")
    return tmp_path


def test_clean_yes_flag_deletes_without_question(folder_with_bak):
    assert main(["clean", str(folder_with_bak), "--yes"]) == 0
    assert not (folder_with_bak / "a.fb2.bak").exists()
    assert (folder_with_bak / "book.fb2").exists()


def test_clean_answer_no_keeps_files(folder_with_bak, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    assert main(["clean", str(folder_with_bak)]) == 0
    assert (folder_with_bak / "a.fb2.bak").exists()


def test_clean_russian_answer_deletes(folder_with_bak, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt="": "да")
    assert main(["clean", str(folder_with_bak)]) == 0
    assert not (folder_with_bak / "a.fb2.bak").exists()


def test_clean_without_input_keeps_files(folder_with_bak, monkeypatch):
    def no_input(prompt=""):
        raise EOFError

    monkeypatch.setattr("builtins.input", no_input)
    assert main(["clean", str(folder_with_bak)]) == 0
    assert (folder_with_bak / "a.fb2.bak").exists()


def test_clean_when_nothing_to_delete(tmp_path, capsys):
    assert main(["clean", str(tmp_path)]) == 0
    assert "не найдено" in capsys.readouterr().out


@pytest.mark.parametrize("command", ["check", "fix", "clean"])
def test_missing_folder_is_an_error(tmp_path, command):
    assert main([command, str(tmp_path / "нет_такой_папки")]) == 2
