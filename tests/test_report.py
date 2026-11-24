import csv
import json
from pathlib import Path

import pytest

from fb2tools.checker import diagnose_bytes
from fb2tools.cli import main
from fb2tools.report import scan

BODY = "<body><section><p>Текст</p></section></body>".encode("utf-8")


@pytest.fixture
def library(tmp_path, good_fb2):
    """Папка из трёх книг: исправная, чинимая (обрезан тег) и нечинимая (нет <body>)."""
    (tmp_path / "good.fb2").write_bytes(good_fb2)
    (tmp_path / "truncated.fb2").write_bytes(good_fb2.replace(b'link">\n', b""))
    (tmp_path / "nobody.fb2").write_bytes(good_fb2.replace(BODY, b""))
    return tmp_path


@pytest.mark.parametrize("data, code", [
    (b"<FictionBook><description>", "xml_parse"),
    (b"<html><body/></html>", "wrong_root"),
    (
        b'<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">'
        b"<description><title-info><book-title>T</book-title></title-info></description>"
        b"</FictionBook>",
        "no_body",
    ),
    (
        b'<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0">'
        b"<description><title-info><book-title>T</book-title></title-info></description>on>"
        b"<body/></FictionBook>",
        "stray_text",
    ),
])
def test_diagnose_returns_stable_codes(data, code):
    assert code in [p.code for p in diagnose_bytes(data)]


def test_scan_reports_status_and_fixable(library):
    reports = {r.path.name: r for r in scan(library)}
    assert reports["good.fb2"].ok and not reports["good.fb2"].fixable
    assert [p.code for p in reports["truncated.fb2"].problems] == ["xml_parse"]
    assert reports["truncated.fb2"].fixable
    assert [p.code for p in reports["nobody.fb2"].problems] == ["no_body"]
    assert not reports["nobody.fb2"].fixable


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_csv_report_lists_only_problem_files(library, tmp_path):
    out = tmp_path / "report.csv"
    assert main(["check", str(library), "--format", "csv", "--output", str(out)]) == 1
    assert out.read_bytes().startswith(b"\xef\xbb\xbf")  # BOM для Excel
    rows = {Path(r["path"]).name: r for r in read_csv(out)}
    assert set(rows) == {"truncated.fb2", "nobody.fb2"}
    assert rows["truncated.fb2"]["code"] == "xml_parse"
    assert rows["truncated.fb2"]["fixable"] == "yes"
    assert rows["nobody.fb2"]["status"] == "error"
    assert rows["nobody.fb2"]["fixable"] == "no"


def test_csv_report_with_all_includes_ok_files(library, tmp_path):
    out = tmp_path / "report.csv"
    main(["check", str(library), "--format", "csv", "--all", "--output", str(out)])
    rows = {Path(r["path"]).name: r for r in read_csv(out)}
    assert rows["good.fb2"]["status"] == "ok"
    assert rows["good.fb2"]["code"] == ""


def test_csv_report_for_clean_library_has_only_header(tmp_path, good_fb2):
    (tmp_path / "good.fb2").write_bytes(good_fb2)
    out = tmp_path / "report.csv"
    assert main(["check", str(tmp_path), "--format", "csv", "--output", str(out)]) == 0
    assert read_csv(out) == []


def test_json_report_structure(library, tmp_path):
    out = tmp_path / "report.json"
    assert main(["check", str(library), "--format", "json", "--output", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["total"] == 3 and data["with_errors"] == 2
    assert data["folder"] == str(library)
    assert {"generated", "tool_version"} <= set(data)
    files = {Path(f["path"]).name: f for f in data["files"]}
    assert set(files) == {"truncated.fb2", "nobody.fb2"}
    assert files["truncated.fb2"]["ok"] is False
    assert files["truncated.fb2"]["fixable"] is True
    assert files["nobody.fb2"]["problems"][0]["code"] == "no_body"


def test_json_report_with_all_includes_ok_files(library, tmp_path):
    out = tmp_path / "report.json"
    main(["check", str(library), "--format", "json", "--all", "--output", str(out)])
    files = {Path(f["path"]).name: f for f in json.loads(out.read_text("utf-8"))["files"]}
    assert files["good.fb2"]["ok"] is True
    assert files["good.fb2"]["problems"] == []


def test_json_to_stdout_is_valid_json(library, capsys):
    main(["check", str(library), "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert data["with_errors"] == 2


def test_text_format_is_default_and_readable(library, capsys):
    assert main(["check", str(library)]) == 1
    out = capsys.readouterr().out
    assert "truncated.fb2" in out
    assert "    - XML не разбирается" in out
    assert "good.fb2" not in out


def test_unwritable_output_is_an_error(library, tmp_path):
    bad_output = tmp_path / "нет_такой_папки" / "report.csv"
    assert main(["check", str(library), "--format", "csv", "--output", str(bad_output)]) == 2
