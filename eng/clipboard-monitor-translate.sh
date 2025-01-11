#!/usr/bin/env bash

#shellcheck source=../.qfuncs.sh
source ~/.qfuncs.sh

set -e

yellow="\033[0;33m"
reset="\033[0m"

hline () {
   # prints a horizontal line the width of the terminal
   cols="$(tput cols)"
   printf '%*s\n' "$cols" '' | tr ' ' '-'
}

_os="$(uname)"
if [[ "$(uname)" != "Darwin" ]]; then
   printf '%s%s%s%s\n' "$yellow" "⚠️" "Sorry, this is only implemented for macOS currently" "$reset"
   exit 1
fi

if [ $# -eq 0 ] || [[ $1 =~ ^--?h(elp)?$ ]]; then
   cat - <<EOM
Monitors the clipboard for changes and translates the text to the target language in real-time.
USAGE:
   $cmd_base [TARGET_LANGUAGE]
EOM
   exit 1
fi

if [ -z "$1" ]; then
   printf '%s%s%s%s\n' "$yellow" "⚠️" "Please provide a target language" "$reset"
   exit 1
fi

cd "$(dirname "$(dirname "$0")")" || exit 1
# shellcheck source=../venv/bin/activate
source venv/bin/activate

target_lang="$1"

# Translate the clipboard text
while true; do
   mapfile clipboard_text < <(pbpaste)
   md5_clipboard_text="$(md5 -q <<<"${clipboard_text[*]}")"
   if [ "$md5_clipboard_text" != "$old_clipboard_md5" ]; then
      if [ -n "${clipboard_text[*]}" ]; then
         python3 -m eng --target "$target_lang" -v <<<"${clipboard_text[*]}"
         hline
      fi
      read -r old_clipboard_md5 <<<"$(md5 -q <<<"${clipboard_text[*]}")"
   fi
   sleep 1
done
