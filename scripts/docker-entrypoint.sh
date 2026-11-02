#!/bin/sh
# Identity bootstrap only: never modify model files, passwd/group or mount permissions.
set -eu
PUID=${PUID-99}
PGID=${PGID-100}
validate_id() {
    case "$2" in
        ''|*[!0-9]*|0*) echo "$1: expected canonical decimal ID 1..2147483647 (root is forbidden)" >&2; exit 2 ;;
    esac
    if [ "${#2}" -gt 10 ] || [ "$2" -gt 2147483647 ]; then
        echo "$1: expected decimal ID 1..2147483647" >&2
        exit 2
    fi
}
validate_id PUID "$PUID"
validate_id PGID "$PGID"
export PUID PGID
if [ "$(id -u)" = 0 ]; then
    # Only SETUID and SETGID are needed. Effective/permitted capabilities are cleared
    # by the nonzero UID transition; no_new_privs prevents gaining them back on exec.
    exec setpriv --reuid "$PUID" --regid "$PGID" --clear-groups \
        --inh-caps=-all --ambient-caps=-all --no-new-privs \
        /usr/local/bin/nemotron-wyoming "$@"
fi
if [ "$(id -u)" != "$PUID" ] || [ "$(id -g)" != "$PGID" ]; then
    echo "PUID/PGID do not match Docker --user; use matching IDs or allow bootstrap SETUID/SETGID" >&2
    exit 2
fi
exec setpriv --no-new-privs /usr/local/bin/nemotron-wyoming "$@"
