# Cofre de IA

Sistema privado para guardar **prompts**, **ideias de IA** e **links**, com login. Feito em Django.

## Usar no seu computador (Windows)

Abra o PowerShell na pasta do projeto e rode:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Abra http://127.0.0.1:8000 no navegador. Para parar, use `Ctrl + C`.

## Criar os usuários (você e seu irmão)

Não existe cadastro público. Cada usuário é criado por você, uma vez:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

O programa pergunta usuário, e-mail (pode deixar vazio) e senha (mínimo de 10 caracteres). A senha não aparece enquanto você digita. Repita para o seu irmão.

## Testes

```powershell
.\.venv\Scripts\python.exe manage.py test
```

## Publicar na VPS (resumo, o passo a passo será feito juntos)

1. VPS Ubuntu 24.04 + domínio apontando para o IP dela.
2. Instalar: `python3-venv`, `caddy`, `sqlite3`, `git`.
3. Copiar o projeto para `/home/cofre/app`, criar `.venv` e instalar `requirements.txt`.
4. Criar `.env` a partir de `.env.example` (com uma `SECRET_KEY` nova).
5. `python manage.py migrate`, `python manage.py collectstatic`, `python manage.py createsuperuser`.
6. Ativar `deploy/cofre.service` (systemd) e `deploy/Caddyfile`.
7. Agendar `deploy/backup.sh` diariamente (cron).

## Segurança

- Todas as páginas exigem login; 5 senhas erradas bloqueiam por 1 hora.
- O arquivo `.env` e o banco `db.sqlite3` nunca devem ser compartilhados nem enviados a repositórios públicos.
