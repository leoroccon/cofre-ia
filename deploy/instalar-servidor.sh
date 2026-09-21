#!/bin/bash
# Instala o Cofre de IA num servidor Ubuntu 24.04 novo.
#
# Como usar (como root, com o projeto já copiado para /home/cofre/app):
#   DOMINIO=meusite.com.br bash /home/cofre/app/deploy/instalar-servidor.sh
#
# Sem domínio ainda? Use o endereço com o IP, que também ganha o cadeado (HTTPS):
#   DOMINIO=203-0-113-10.sslip.io bash /home/cofre/app/deploy/instalar-servidor.sh
#
# Pode rodar de novo com segurança: ele atualiza sem apagar o banco nem o .env.
set -euo pipefail

: "${DOMINIO:?Defina DOMINIO. Ex.: DOMINIO=meusite.com.br}"
APP=/home/cofre/app

[ "$(id -u)" -eq 0 ] || { echo "Rode como root."; exit 1; }
[ -f "$APP/manage.py" ] || { echo "Copie o projeto para $APP antes de rodar."; exit 1; }

export DEBIAN_FRONTEND=noninteractive
echo "==> Instalando programas..."
apt-get update -y
apt-get install -y python3-venv python3-pip sqlite3 caddy ufw fail2ban unattended-upgrades

echo "==> Criando o usuário 'cofre' (sem senha; só o site roda com ele)..."
id cofre >/dev/null 2>&1 || adduser --disabled-password --gecos "" cofre
chown -R cofre:cofre /home/cofre

echo "==> Preparando o Python e as dependências..."
sudo -u cofre bash -c "cd $APP && python3 -m venv .venv && .venv/bin/pip install -q --upgrade pip && .venv/bin/pip install -q -r requirements.txt"

if [ ! -f "$APP/.env" ]; then
  echo "==> Criando o .env com uma chave secreta nova..."
  CHAVE=$(python3 -c 'import secrets; print(secrets.token_urlsafe(60))')
  cat > "$APP/.env" <<EOF
DEBUG=False
SECRET_KEY=$CHAVE
ALLOWED_HOSTS=$DOMINIO
CSRF_TRUSTED_ORIGINS=https://$DOMINIO
EOF
  chown cofre:cofre "$APP/.env"
  chmod 600 "$APP/.env"
fi

echo "==> Criando o banco e juntando os arquivos do site..."
sudo -u cofre bash -c "cd $APP && .venv/bin/python manage.py migrate --noinput && .venv/bin/python manage.py collectstatic --noinput"

echo "==> Ligando o site como serviço (reinicia sozinho se cair ou se o servidor reiniciar)..."
cp "$APP/deploy/cofre.service" /etc/systemd/system/cofre.service
systemctl daemon-reload
systemctl enable cofre
systemctl restart cofre

echo "==> Configurando o Caddy (HTTPS automático) para $DOMINIO..."
cat > /etc/caddy/Caddyfile <<EOF
$DOMINIO {
	encode gzip
	reverse_proxy 127.0.0.1:8000
}
EOF
systemctl enable caddy
systemctl restart caddy

echo "==> Firewall: só SSH (22), HTTP (80) e HTTPS (443)..."
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "==> Backup diário do banco às 3h30 (guarda 14 dias)..."
cp "$APP/deploy/backup.sh" /home/cofre/backup.sh
chown cofre:cofre /home/cofre/backup.sh
chmod +x /home/cofre/backup.sh
( crontab -u cofre -l 2>/dev/null | grep -v backup.sh || true; echo "30 3 * * * /home/cofre/backup.sh" ) | crontab -u cofre -

echo
echo "Pronto! Abra: https://$DOMINIO"
echo "Falta criar os usuários (você digita a senha, ninguém mais precisa vê-la):"
echo "  su - cofre -c 'cd app && .venv/bin/python manage.py createsuperuser'"
