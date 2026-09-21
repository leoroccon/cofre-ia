#!/bin/bash
# Backup diário do banco. Guarda os últimos 14 dias em /home/cofre/backups.
set -e
DESTINO=/home/cofre/backups
mkdir -p "$DESTINO"
sqlite3 /home/cofre/app/db.sqlite3 ".backup '$DESTINO/db-$(date +%F).sqlite3'"
find "$DESTINO" -name 'db-*.sqlite3' -mtime +14 -delete
