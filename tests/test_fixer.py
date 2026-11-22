from fb2tools.checker import check_bytes
from fb2tools.fixer import parses, process_file, repair

# Обрезанный корневой тег: после ".../1999/x" сразу идёт <description>
TRUNCATED_ROOT = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" '
    'xmlns:l="http://www.w3.org/1999/x'
    "<description><title-info><book-title>Тест</book-title></title-info></description>\n"
    "<body><section><p>Текст</p></section></body>\n"
    "</FictionBook>\n"
).encode("utf-8")

# Мусор сразу после </description>
GARBAGE_TAIL = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" '
    'xmlns:l="http://www.w3.org/1999/xlink">\n'
    "<description><title-info><book-title>Тест</book-title></title-info></description>on>on>on>"
    "<body><section><p>Текст</p></section></body>\n"
    "</FictionBook>\n"
).encode("utf-8")

# Правило сработает, но файл всё равно останется битым (незакрытый <oops>)
UNFIXABLE = (
    '<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" '
    "<description><oops></description>"
).encode("utf-8")


def test_repair_truncated_root():
    assert not parses(TRUNCATED_ROOT)
    fixed, notes = repair(TRUNCATED_ROOT)
    assert notes == ["обрезанный тег <FictionBook>"]
    assert parses(fixed)
    assert check_bytes(fixed) == []


def test_repair_garbage_after_description():
    assert "посторонний текст внутри <FictionBook>" in check_bytes(GARBAGE_TAIL)
    fixed, notes = repair(GARBAGE_TAIL)
    assert notes == ["мусор после </description>"]
    assert parses(fixed)
    assert check_bytes(fixed) == []


def test_repair_leaves_good_file_alone(good_fb2):
    fixed, notes = repair(good_fb2)
    assert notes == []
    assert fixed == good_fb2


def test_process_file_dry_run_does_not_modify(tmp_path):
    path = tmp_path / "book.fb2"
    path.write_bytes(TRUNCATED_ROOT)
    result = process_file(path, apply=False)
    assert result is not None and result.resolved and not result.written
    assert path.read_bytes() == TRUNCATED_ROOT
    assert not (tmp_path / "book.fb2.bak").exists()


def test_process_file_apply_fixes_and_makes_backup(tmp_path):
    path = tmp_path / "book.fb2"
    path.write_bytes(TRUNCATED_ROOT)
    result = process_file(path, apply=True)
    assert result is not None and result.written
    assert (tmp_path / "book.fb2.bak").read_bytes() == TRUNCATED_ROOT
    assert check_bytes(path.read_bytes()) == []


def test_process_file_unfixable_is_left_untouched(tmp_path):
    path = tmp_path / "bad.fb2"
    path.write_bytes(UNFIXABLE)
    result = process_file(path, apply=True)
    assert result is not None and not result.resolved and not result.written
    assert path.read_bytes() == UNFIXABLE
    assert not (tmp_path / "bad.fb2.bak").exists()
