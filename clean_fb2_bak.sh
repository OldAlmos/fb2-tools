#!/usr/bin/env bash
# Удаление резервных копий *.fb2.bak
# Использование: clean_fb2_bak.sh [ПАПКА] [--yes]

dir="${1:-.}"
[ "$1" = "--yes" ] && dir="."

if [ ! -d "$dir" ]; then
    echo "Папка не найдена: $dir" >&2
    exit 1
fi

mapfile -d '' files < <(find "$dir" -type f -name '*.fb2.bak' -print0)

if [ "${#files[@]}" -eq 0 ]; then
    echo "Файлов *.fb2.bak не найдено."
    exit 0
fi

printf '%s\n' "${files[@]}"
echo
echo "Найдено файлов: ${#files[@]}"

if [[ " $* " != *" --yes "* ]]; then
    read -r -p "Удалить их? [y/N] " answer
    case "$answer" in
        y|Y|yes|YES|д|Д|да|Да|ДА) ;;
        *) echo "Отменено."; exit 0 ;;
    esac
fi

printf '%s\0' "${files[@]}" | xargs -0 rm -v --
echo "Готово."
