#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Usage: $(basename "$0") <command> [options]

Commands:
  push          Copy all local files/folders to the remote
  push --clean  Wipe the remote filesystem, then push
  pull          Copy all remote files/folders to the current directory

Options:
  -p, --port <port>   Serial port (e.g. /dev/ttyUSB0). Auto-detected if omitted.

Examples:
  $(basename "$0") push
  $(basename "$0") push --clean
  $(basename "$0") pull
  $(basename "$0") push -p /dev/ttyUSB0
  $(basename "$0") push --clean --port /dev/cu.usbmodem1101
EOF
  exit 1
}

COMMAND=""
PORT=""
CLEAN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    push|pull)
      COMMAND="$1"
      shift
      ;;
    --clean)
      CLEAN=true
      shift
      ;;
    -p|--port)
      PORT="${2:-}"
      [[ -z "$PORT" ]] && { echo "Error: --port requires a value"; exit 1; }
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      ;;
  esac
done

[[ -z "$COMMAND" ]] && usage

if [[ -n "$PORT" ]]; then
  MPREMOTE="mpremote connect $PORT"
else
  MPREMOTE="mpremote"
fi

LOCAL_DIR="$(pwd)"

case "$COMMAND" in
  push)
    echo "Pushing '$LOCAL_DIR' → remote:/"
    if $CLEAN; then
      echo "Wiping remote filesystem..."
      $MPREMOTE rm -rv :
    fi
    $MPREMOTE cp -r ./app/* :
    ;;
  pull)
    echo "Pulling remote:/ → '$LOCAL_DIR'"
    $MPREMOTE cp -r : ./app/
    ;;
esac

echo "Done."
