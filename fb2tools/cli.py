"""Командная строка: fb2tools check|fix|clean ПАПКА."""
import argparse
import sys
from pathlib import Path

from . import __version__
from .cleaner import delete_files, iter_bak_files
from .fixer import process_file
from .report import FORMATS, render, scan

YES_ANSWERS = {"y", "yes", "д", "да"}


def _folder_exists(folder: Path) -> bool:
    if folder.is_dir():
        return True
    print(f"Папка не найдена: {folder}", file=sys.stderr)
    return False


def cmd_check(args: argparse.Namespace) -> int:
    if not _folder_exists(args.folder):
        return 2
    reports = scan(args.folder)
    bad = sum(1 for r in reports if not r.ok)

    if args.output:
        # CSV с BOM (utf-8-sig), чтобы Excel на Windows правильно показал кириллицу
        encoding = "utf-8-sig" if args.format == "csv" else "utf-8"
        try:
            with open(args.output, "w", encoding=encoding, newline="") as f:
                render(args.format, args.folder, reports, f,
                       include_ok=args.all, to_file=True)
        except OSError as e:
            print(f"Не удалось записать отчёт: {e}", file=sys.stderr)
            return 2
        print(f"Отчёт сохранён: {args.output}", file=sys.stderr)
    else:
        render(args.format, args.folder, reports, sys.stdout, include_ok=args.all)

    print(f"\nПроверено: {len(reports)}, с ошибками: {bad}", file=sys.stderr)
    return 1 if bad else 0


def cmd_fix(args: argparse.Namespace) -> int:
    if not _folder_exists(args.folder):
        return 2
    found = fixed = unresolved = 0
    for path in sorted(args.folder.rglob("*")):
        if not path.is_file() or path.suffix.lower() != ".fb2":
            continue
        result = process_file(path, apply=args.fix)
        if result is None:
            continue
        found += 1
        print(f"{path}: {', '.join(result.notes)}")
        if not result.resolved:
            unresolved += 1
            print("    ! после правки XML всё ещё не разбирается, файл не тронут")
        elif result.written:
            fixed += 1

    suffix = "" if args.fix else " (пробный запуск, добавьте --fix)"
    print(f"\nНайдено: {found}, исправлено: {fixed}, "
          f"не удалось исправить: {unresolved}{suffix}")
    return 0


def cmd_clean(args: argparse.Namespace) -> int:
    if not _folder_exists(args.folder):
        return 2
    files = list(iter_bak_files(args.folder))
    if not files:
        print("Файлов *.fb2.bak не найдено.")
        return 0

    for path in files:
        print(path)
    print(f"\nНайдено файлов: {len(files)}")

    if not args.yes:
        try:
            answer = input("Удалить их? [y/N] ")
        except EOFError:  # ввод недоступен (например, запуск из cron): ничего не удаляем
            answer = ""
        if answer.strip().lower() not in YES_ANSWERS:
            print("Отменено.")
            return 0

    deleted, failed = delete_files(files)
    print(f"Удалено: {len(deleted)}")
    for path, reason in failed:
        print(f"Не удалось удалить {path}: {reason}", file=sys.stderr)
    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fb2tools", description="Проверка и починка FB2-файлов")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="найти файлы с ошибками (ничего не меняет)")
    p_check.add_argument("folder", nargs="?", type=Path, default=Path("."))
    p_check.add_argument("--format", choices=FORMATS, default="text",
                         help="формат отчёта (по умолчанию text)")
    p_check.add_argument("-o", "--output", type=Path,
                         help="сохранить отчёт в файл (рекомендуется для csv и json)")
    p_check.add_argument("--all", action="store_true",
                         help="для csv и json: включить и файлы без ошибок")
    p_check.set_defaults(func=cmd_check)

    p_fix = sub.add_parser("fix", help="починить известные повреждения")
    p_fix.add_argument("folder", nargs="?", type=Path, default=Path("."))
    p_fix.add_argument("--fix", action="store_true",
                       help="реально изменить файлы (без флага только показывает)")
    p_fix.set_defaults(func=cmd_fix)

    p_clean = sub.add_parser("clean", help="удалить резервные копии *.fb2.bak")
    p_clean.add_argument("folder", nargs="?", type=Path, default=Path("."))
    p_clean.add_argument("-y", "--yes", action="store_true",
                         help="удалять без подтверждения")
    p_clean.set_defaults(func=cmd_clean)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
