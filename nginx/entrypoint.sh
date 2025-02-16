#!/usr/bin/env sh

inotifywait -m -e close_write /etc/nginx/conf.d/ | while read path action file; do
  echo "[inotify] Detected a change in $path$file — reloading Nginx..."
  nginx -s reload
done &

exec "$@"
