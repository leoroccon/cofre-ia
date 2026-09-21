# Cofre de IA

Site privado para guardar **prompts**, **ideias de IA** e **links**. Feito com Django, com login obrigatório: só quem tem usuário e senha vê o conteúdo.

O conteúdo é compartilhado entre os usuários do cofre (feito para uso em dupla) e cada item mostra quem o criou.

## O que ele faz

**Três áreas, com a mesma interface.** Cada área mostra os itens agrupados, em linhas compactas, com busca e filtro por etiqueta.

| Área | Agrupada por | Ao clicar na linha |
|---|---|---|
| **Prompts** | categoria | copia o texto do prompt e mostra "Copiado" |
| **Ideias de IA** | status (rascunho, em teste, feita) | nada |
| **Links** | primeira etiqueta | abre o endereço em outra aba |

- **Prompts** têm título, descrição (para que serve), texto, ferramenta, categoria, etiquetas e favorito. A lista mostra só a descrição; o texto completo abre em página própria, com botão **Copiar**.
- **Busca** procura em todos os campos de texto. Ao clicar numa etiqueta, ela vira um filtro dentro da caixa de busca.
- **Área do usuário** (clique no seu nome, no topo): escolher o tema, mudar o nome de usuário e mudar a senha.

### Dois temas

Cada usuário escolhe o seu.

- **Circuito:** fundo de placa de circuito animado. Pulsos de luz correm pelas trilhas, e o cursor "esquenta" as trilhas próximas, em tom de coral, que esfriam devagar.
- **Paisagismo:** uma praça vista de cima, com árvores em croqui, flores, um banco e bolinhas passeando pelos caminhos. As árvores balançam ao vento e reagem ao cursor: deixam cair folhas ao pé e, às vezes, soltam um passarinho.

Cada tema tem o seu cursor. Quem desativa animações no sistema recebe o site com o movimento parado.

## Tecnologias

- Python 3.12 e **Django 6**
- **django-axes**: bloqueia o acesso por 1 hora após 5 senhas erradas
- **WhiteNoise** para os arquivos estáticos
- **SQLite** (suficiente para poucos usuários)
- JavaScript e CSS puros, sem bibliotecas de front-end

## Rodar no seu computador (Windows)

Precisa do Python 3.12. Na pasta do projeto, no PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Abra http://127.0.0.1:8000 e entre com o usuário criado.

**Não existe cadastro público.** Cada usuário é criado por quem administra, com o comando `createsuperuser` (ou pelo painel em `/admin/`). A senha precisa ter pelo menos 10 caracteres.

### Testes

```powershell
.\.venv\Scripts\python.exe manage.py test
```

Os testes cobrem: acesso exigindo login, criar/editar/excluir nas três áreas, busca e etiquetas, agrupamentos e a área do usuário (tema, nome e senha).

## Segurança

- Todas as páginas exigem login, e não há cadastro público.
- 5 tentativas erradas bloqueiam o acesso por 1 hora (por IP e usuário).
- Senhas com no mínimo 10 caracteres, sem senhas comuns nem só números.
- O `.env` e o banco de dados **nunca** vão para o Git (veja `.gitignore`).

## Estrutura

```
cofre/     configurações do projeto Django (settings, urls)
acervo/    o aplicativo: modelos, telas, formulários, testes
  static/acervo/   estilo.css, vida.js (animações) e as cenas dos temas (SVG)
  templates/       páginas HTML
```

Os temas são só variáveis de cor no `estilo.css`. Para criar um tema novo, adicione uma opção em `Perfil.Tema` (`acervo/models.py`) e um bloco `body.tema-<nome>` no CSS.
