#!/usr/bin/env bash
# Lance l'application Dazzle Dash : http://127.0.0.1:8050 (Ctrl+C pour l'arrêter).
# Si une ancienne copie de l'appli de ce projet est restée ouverte, elle est arrêtée d'abord.

set -euo pipefail

# Se placer à la racine du projet, d'où que le script soit lancé.
cd "$(dirname "$0")/.."
PROJECT_DIR="$(pwd)"
PORT="${PORT:-8050}"

old_pid="$(lsof -t -iTCP:"$PORT" -sTCP:LISTEN || true)"
if [ -n "$old_pid" ]; then
  old_cmd="$(ps -o command= -p "$old_pid")"
  old_dir="$(lsof -a -p "$old_pid" -d cwd -Fn | sed -n 's/^n//p')"
  # On n'arrête que notre propre appli (index.py lancé depuis ce dossier), jamais un autre programme.
  if [[ "$old_cmd" == *index.py* && "$old_dir" == "$PROJECT_DIR" ]]; then
    echo "Ancienne appli encore ouverte sur le port $PORT (processus $old_pid) : je l'arrête."
    kill "$old_pid"
    # Attendre que le port se libère (5 secondes maximum).
    for _ in 1 2 3 4 5 6 7 8 9 10; do
      lsof -t -iTCP:"$PORT" -sTCP:LISTEN > /dev/null || break
      sleep 0.5
    done
  else
    echo "Le port $PORT est pris par un autre programme (processus $old_pid) : $old_cmd" >&2
    echo "Arrête-le, ou lance sur un autre port : PORT=8060 ./scripts/run_app.sh" >&2
    exit 1
  fi
fi

echo "Application : http://127.0.0.1:$PORT   (Ctrl+C pour l'arrêter)"
# exec : le script laisse sa place à l'appli, donc Ctrl+C l'arrête directement, sans rien laisser derrière.
exec env PORT="$PORT" uv run python index.py
