"""Enche o cofre com itens de exemplo, para ver as telas com conteúdo de verdade.

    python manage.py semear
    python manage.py semear --limpar

Rodar duas vezes não duplica nada: o que já existe (mesmo título) é deixado como está,
inclusive se você tiver editado. O `--limpar` remove só os itens desta lista.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from acervo.models import Ideia, Link, Prompt

# título, categoria, ferramenta, etiquetas, favorito, descrição, texto
PROMPTS = [
    ("Revisor de texto claro", "Escrita", "Claude", "revisão, português, clareza", True,
     "Deixa qualquer texto mais direto sem perder o sentido original.",
     "Revise o texto abaixo deixando-o mais claro e direto. Mantenha o sentido e o tom do autor. "
     "Corte redundâncias, troque jargão por palavra simples e quebre frases longas. "
     "Ao final, liste em tópicos o que você mudou e por quê.\n\nTexto:\n{texto}"),
    ("Resumo em três camadas", "Escrita", "Claude", "resumo, leitura", False,
     "Resume um texto em uma frase, um parágrafo e um tópico por seção.",
     "Resuma o texto a seguir em três camadas:\n1. Uma frase (o essencial).\n2. Um parágrafo (até 80 palavras).\n"
     "3. Um tópico por seção, na ordem do original.\nNão acrescente nada que não esteja no texto.\n\n{texto}"),
    ("E-mail difícil", "Escrita", "ChatGPT", "e-mail, trabalho, comunicação", False,
     "Escreve e-mails delicados (cobrança, recusa, atraso) sem soar agressivo.",
     "Escreva um e-mail profissional em português do Brasil sobre a situação abaixo. "
     "Seja direto e cordial, sem rodeios nem desculpas excessivas. Máximo de 150 palavras. "
     "Termine com um próximo passo concreto.\n\nSituação: {situacao}\nDestinatário: {destinatario}"),
    ("Título que não é caça-clique", "Escrita", "Claude", "título, copy", False,
     "Gera 10 títulos honestos para um artigo, do mais sóbrio ao mais chamativo.",
     "Gere 10 títulos para o artigo descrito abaixo, ordenados do mais sóbrio ao mais chamativo. "
     "Nenhum pode prometer o que o texto não entrega. Máximo de 70 caracteres cada.\n\nArtigo: {resumo}"),
    ("Tradução com contexto", "Escrita", "Claude", "tradução, inglês", False,
     "Traduz mantendo o registro e explicando as escolhas duvidosas.",
     "Traduza o texto de {origem} para {destino}. Mantenha o registro (formal/informal) do original. "
     "Quando uma expressão não tiver equivalente direto, escolha a melhor opção e explique em nota de rodapé.\n\n{texto}"),
    ("Explica este código", "Código", "Claude", "código, leitura, onboarding", True,
     "Explica um trecho de código de cima para baixo, com as armadilhas.",
     "Explique o código abaixo para alguém que conhece a linguagem mas não este projeto.\n"
     "1. O que ele faz, em uma frase.\n2. O fluxo, passo a passo.\n3. Pontos em que é fácil errar ao mexer.\n"
     "Não sugira melhorias ainda.\n\n{codigo}"),
    ("Revisão de PR", "Código", "Claude", "código, revisão, qualidade", True,
     "Revisa um diff procurando bugs reais, não estilo.",
     "Revise o diff abaixo procurando apenas problemas de correção: bugs, casos de borda não tratados, "
     "condições de corrida, erros de tipo. Ignore formatação e preferências de estilo. "
     "Para cada achado, descreva a entrada concreta que provoca a falha. Se não houver nada, diga isso.\n\n{diff}"),
    ("Teste antes do código", "Código", "Claude", "código, testes, tdd", False,
     "Escreve os testes que descrevem o comportamento desejado.",
     "Escreva testes para a funcionalidade descrita abaixo, antes da implementação. "
     "Cubra o caminho feliz, os casos de borda e os erros esperados. "
     "Use {framework}. Nomes de teste devem descrever o comportamento, não o método.\n\nFuncionalidade: {descricao}"),
    ("Mensagem de commit", "Código", "Claude", "git, código", False,
     "Transforma um diff em mensagem de commit no padrão do projeto.",
     "Escreva a mensagem de commit para o diff abaixo. Primeira linha no imperativo, até 72 caracteres. "
     "Depois, um parágrafo curto dizendo por que a mudança foi feita (não o que ela faz — isso o diff já mostra).\n\n{diff}"),
    ("Caçador de regressão", "Código", "Claude", "código, depuração", False,
     "Ajuda a achar quando e por que algo parou de funcionar.",
     "Estou com este comportamento errado: {sintoma}\nEsperado: {esperado}\n"
     "Liste as 5 causas mais prováveis em ordem de probabilidade. Para cada uma, diga qual comando ou teste "
     "confirma ou descarta a hipótese no menor tempo possível."),
    ("SQL explicado", "Código", "ChatGPT", "sql, banco de dados", False,
     "Escreve a consulta e explica onde ela pode ficar lenta.",
     "Escreva uma consulta SQL para: {objetivo}\nEsquema:\n{esquema}\n"
     "Depois da consulta, explique em português o que cada junção faz e onde ela pode ficar lenta."),
    ("Regex sem dor", "Código", "Claude", "regex, código", False,
     "Monta e explica uma expressão regular, com casos de teste.",
     "Monte uma expressão regular que case com: {alvo}\nE que NÃO case com: {nao_alvo}\n"
     "Explique cada parte da expressão e liste 6 casos de teste, 3 que passam e 3 que não."),
    ("Croqui arquitetônico", "Imagem", "Midjourney", "arquitetura, render, croqui", True,
     "Render de croqui de fachada, traço solto e aquarelado.",
     "architectural sketch of {edificio}, loose ink linework, light watercolor wash, warm afternoon light, "
     "human figures for scale, white background, hand-drawn feel --ar 3:2 --style raw"),
    ("Planta humanizada", "Imagem", "Midjourney", "arquitetura, planta, paisagismo", False,
     "Planta baixa humanizada vista de cima, estilo croqui.",
     "top-down humanized floor plan of {espaco}, hand-drawn style, soft pastel tones, furniture and plants "
     "indicated loosely, subtle paper texture --ar 1:1 --style raw"),
    ("Foto de produto limpa", "Imagem", "Midjourney", "produto, foto, e-commerce", False,
     "Produto em fundo neutro, luz de estúdio suave.",
     "product photography of {produto}, seamless neutral background, soft studio lighting from the left, "
     "subtle shadow, 85mm lens, high detail --ar 4:5"),
    ("Ilustração para artigo", "Imagem", "Midjourney", "ilustração, editorial", False,
     "Ilustração editorial conceitual, paleta reduzida.",
     "editorial illustration about {tema}, conceptual and minimal, limited palette of three colors, "
     "flat shapes with grain texture, generous negative space --ar 16:9"),
    ("Textura sem emenda", "Imagem", "Midjourney", "textura, material", False,
     "Textura que repete sem costura aparente.",
     "seamless tileable texture of {material}, top-down, even diffuse lighting, no shadows, "
     "photorealistic, 4k --tile"),
    ("Pesquisa com fontes", "Pesquisa", "Claude", "pesquisa, fontes", True,
     "Levanta um tema citando de onde veio cada afirmação.",
     "Pesquise sobre: {tema}\nPara cada afirmação, indique a fonte. Separe o que é consenso do que é disputado. "
     "Ao final, liste o que você NÃO conseguiu confirmar. Não preencha lacunas com suposição."),
    ("Comparador de opções", "Pesquisa", "Claude", "decisão, comparação", False,
     "Compara alternativas por critérios explícitos.",
     "Compare {opcoes} para o caso de uso: {caso}\nMonte uma tabela com os critérios que importam nesse caso "
     "(escolha-os e justifique). Termine com uma recomendação e a condição que a mudaria."),
    ("Advogado do diabo", "Pesquisa", "Claude", "decisão, crítica", False,
     "Ataca uma ideia sua para ver se ela aguenta.",
     "Vou descrever uma decisão que pretendo tomar. Ataque-a: aponte as suposições frágeis, o que pode dar errado "
     "e o cenário em que ela é claramente a escolha errada. Não amenize.\n\nDecisão: {decisao}"),
    ("Linha do tempo", "Pesquisa", "Claude", "pesquisa, história", False,
     "Monta cronologia de um assunto com os marcos que importam.",
     "Monte uma linha do tempo de {assunto}. Inclua só os marcos que mudaram o rumo do assunto, "
     "com data e uma frase dizendo o que mudou. Máximo de 15 itens."),
    ("Glossário do domínio", "Pesquisa", "Claude", "glossário, estudo", False,
     "Explica o vocabulário de uma área para quem chega agora.",
     "Sou novo em {area}. Liste os 20 termos que mais aparecem e que um iniciante entende errado. "
     "Para cada um: definição em uma frase, o erro comum e um exemplo."),
    ("Proposta comercial", "Negócios", "Claude", "proposta, cliente, orçamento", True,
     "Estrutura uma proposta com escopo, prazo e o que não está incluso.",
     "Escreva uma proposta comercial para o serviço abaixo. Estruture em: entendimento do problema, escopo, "
     "entregas, prazo, investimento e — importante — o que NÃO está incluso. "
     "Tom profissional e direto.\n\nServiço: {servico}\nCliente: {cliente}"),
    ("Briefing de projeto", "Negócios", "Claude", "briefing, cliente", False,
     "Vira uma conversa solta com o cliente num briefing organizado.",
     "Organize as anotações abaixo em um briefing: objetivo, público, restrições, referências, "
     "critérios de sucesso e perguntas em aberto. Marque claramente o que o cliente ainda não respondeu.\n\n{notas}"),
    ("Ata de reunião", "Negócios", "Claude", "reunião, ata, trabalho", False,
     "Transforma transcrição em ata com decisões e responsáveis.",
     "Transforme a transcrição abaixo em ata. Seções: decisões tomadas, pendências (com responsável e prazo, "
     "quando ditos) e assuntos adiados. Ignore conversa fiada.\n\n{transcricao}"),
    ("Precificação por valor", "Negócios", "Claude", "preço, freelance", False,
     "Ajuda a pensar preço a partir do valor entregue, não da hora.",
     "Vou descrever um serviço que presto. Ajude-me a precificá-lo por valor: qual problema ele resolve, "
     "quanto esse problema custa ao cliente, que faixas de preço fazem sentido e como apresentar as opções.\n\n{servico}"),
    ("Plano de estudo", "Estudo", "Claude", "estudo, plano, aprendizado", False,
     "Monta um plano de estudo realista para o tempo que você tem.",
     "Quero aprender {assunto} em {prazo}, com {horas} horas por semana. Monte um plano semanal com "
     "o que estudar, o que praticar e como saber que aprendi. Prefira poucos recursos bons a uma lista longa."),
    ("Me explique em três níveis", "Estudo", "Claude", "estudo, explicação", True,
     "Explica um conceito em três profundidades diferentes.",
     "Explique {conceito} em três níveis:\n1. Para quem nunca ouviu falar (analogia do cotidiano).\n"
     "2. Para quem trabalha na área vizinha.\n3. Para quem vai implementar.\nDiga onde a analogia do nível 1 quebra."),
    ("Ficha de leitura", "Estudo", "Claude", "leitura, estudo, resumo", False,
     "Vira um livro ou artigo em ficha com a tese e os contra-argumentos.",
     "Faça a ficha de leitura de {obra}: tese central, argumentos que a sustentam, evidências apresentadas, "
     "contra-argumentos que o autor não enfrenta e três frases que valem citar."),
    ("Perguntas antes da resposta", "Estudo", "Claude", "método, pergunta", False,
     "Força o modelo a perguntar antes de responder de qualquer jeito.",
     "Vou pedir uma tarefa. Antes de executá-la, faça até 5 perguntas cujas respostas mudariam o resultado. "
     "Não faça perguntas cuja resposta você consegue supor com segurança. "
     "Depois que eu responder, execute.\n\nTarefa: {tarefa}"),
]

# título, status, etiquetas, descrição
IDEIAS = [
    ("Bot que resume meus e-mails de manhã", "feita", "automação, e-mail, rotina",
     "Um agente que lê a caixa de entrada às 7h, separa o que precisa de resposta hoje e manda um resumo único no celular."),
    ("Buscador do meu próprio Drive", "teste", "busca, arquivos, rag",
     "Indexar os PDFs e documentos do Drive num banco vetorial para perguntar em linguagem natural onde está aquele contrato."),
    ("Transcrever reuniões e gerar ata sozinho", "feita", "reunião, transcrição, automação",
     "Transcrever o áudio, extrair decisões e pendências, e a ata cai no canal da equipe sem ninguém digitar."),
    ("Assistente de orçamento de obra", "rascunho", "arquitetura, orçamento, planilha",
     "A partir da planta e do memorial, estimar quantitativos e cruzar com tabela de preços para um orçamento preliminar."),
    ("Revisor de contrato que aponta risco", "teste", "jurídico, contrato, revisão",
     "Ler contratos de prestação de serviço e destacar cláusulas fora do padrão de mercado, com o motivo."),
    ("Gerador de croqui a partir da planta", "rascunho", "arquitetura, imagem, croqui",
     "Subir a planta baixa e receber perspectivas de croqui do ambiente, mantendo as proporções reais."),
    ("Catálogo de materiais com foto", "rascunho", "arquitetura, materiais, visão",
     "Fotografar um material na loja e o sistema identificar, buscar ficha técnica e guardar no catálogo do escritório."),
    ("Agente que responde orçamento no WhatsApp", "teste", "atendimento, whatsapp, vendas",
     "Primeiro atendimento automático: entende o pedido, faz as perguntas que faltam e só passa para o humano quando o escopo está claro."),
    ("Diário de bordo do projeto", "feita", "projeto, registro, rotina",
     "Toda decisão tomada no dia vira uma entrada com contexto, para não perder o porquê seis meses depois."),
    ("Detector de prompt que parou de funcionar", "rascunho", "prompt, qualidade, monitoramento",
     "Rodar os prompts salvos contra casos de teste periodicamente e avisar quando a saída mudar de qualidade."),
    ("Tradutor de memorial descritivo", "rascunho", "arquitetura, tradução, documento",
     "Converter memorial técnico em linguagem que o cliente leigo entende, sem perder a informação."),
    ("Comparador de propostas de fornecedor", "teste", "compras, comparação, planilha",
     "Jogar três PDFs de proposta e receber uma tabela comparando escopo, prazo e preço item a item."),
    ("Organizador de referências visuais", "rascunho", "imagem, referência, organização",
     "Pasta de imagens vira uma biblioteca com etiquetas automáticas de estilo, material e paleta."),
    ("Checklist de projeto gerado do escopo", "rascunho", "projeto, checklist, processo",
     "A partir do contrato, gerar a lista de entregas e prazos, e acompanhar o que já saiu."),
    ("Resumo semanal do que eu li", "feita", "leitura, resumo, rotina",
     "Tudo que eu salvei na semana vira um resumo de domingo com o fio condutor entre os textos."),
    ("Pesquisador de norma técnica", "teste", "norma, arquitetura, pesquisa",
     "Perguntar em português o que a norma exige para determinado caso e receber a resposta com o item citado."),
    ("Estimador de tempo de tarefa", "rascunho", "produtividade, estimativa",
     "Usar o histórico de tarefas parecidas para estimar quanto uma nova vai levar de verdade."),
    ("Curador de conteúdo para o Instagram", "rascunho", "redes sociais, conteúdo",
     "Pegar os projetos entregues e propor posts: recorte da imagem, texto e a ordem do carrossel."),
    ("Assistente de licitação", "rascunho", "licitação, documento, leitura",
     "Ler o edital e responder se vale participar: exigências, prazos e o que falta na documentação."),
    ("Base de conhecimento do escritório", "teste", "conhecimento, equipe, busca",
     "Tudo que a equipe já resolveu vira material consultável, para não responder duas vezes a mesma dúvida."),
    ("Gerador de apresentação de projeto", "rascunho", "apresentação, projeto, cliente",
     "Das imagens e do memorial, montar o deck de apresentação para o cliente com a narrativa pronta."),
    ("Monitor de preço de insumo", "rascunho", "compras, preço, monitoramento",
     "Acompanhar o preço dos materiais mais usados e avisar quando variar acima de um limite."),
    ("Revisor de acessibilidade do site", "feita", "acessibilidade, web, qualidade",
     "Rodar o site contra as regras de acessibilidade e explicar cada problema em linguagem simples."),
    ("Assistente de cronograma de obra", "rascunho", "obra, cronograma, planejamento",
     "Do escopo ao cronograma com dependências, e replanejamento quando uma etapa atrasa."),
    ("Extrator de dados de nota fiscal", "teste", "financeiro, ocr, automação",
     "Foto da nota vira linha na planilha, com fornecedor, valor e categoria já preenchidos."),
    ("Simulador de conversa difícil", "rascunho", "comunicação, treino",
     "Treinar uma conversa delicada com o modelo fazendo o papel do outro lado, com feedback ao final."),
    ("Indexador dos meus áudios", "rascunho", "áudio, busca, transcrição",
     "Transcrever os áudios recebidos e tornar tudo pesquisável por assunto."),
    ("Gerador de variações de layout", "rascunho", "arquitetura, layout, geração",
     "Dadas as restrições do terreno e do programa, propor variações de implantação para comparar."),
    ("Leitor de e-mail de cliente com tom", "teste", "e-mail, cliente, análise",
     "Além do conteúdo, apontar se o cliente está insatisfeito e sugerir como responder."),
    ("Arquivo morto pesquisável", "feita", "arquivo, busca, organização",
     "Projetos antigos digitalizados e indexados, para achar aquele detalhe construtivo de anos atrás."),
]

# título, url, etiquetas, descrição
LINKS = [
    ("Documentação do Claude", "https://docs.claude.com/", "documentação, claude, api",
     "Referência oficial da API, do Claude Code e das boas práticas de prompt."),
    ("Engenharia de prompt da Anthropic", "https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview",
     "documentação, prompt, claude",
     "As técnicas que realmente movem a agulha, com exemplos de antes e depois."),
    ("Claude Code", "https://claude.com/claude-code", "ferramenta, claude, código",
     "O agente de programação no terminal, no editor e no navegador."),
    ("Model Context Protocol", "https://modelcontextprotocol.io/", "documentação, mcp, integração",
     "O padrão aberto para conectar modelos a ferramentas e dados."),
    ("Documentação do Django", "https://docs.djangoproject.com/pt-br/stable/", "documentação, django, python",
     "Referência completa, em português, do framework que roda este cofre."),
    ("Tutorial do Django Girls", "https://tutorial.djangogirls.org/pt/", "tutorial, django, iniciante",
     "O melhor caminho de entrada no Django para quem está começando."),
    ("MDN Web Docs", "https://developer.mozilla.org/pt-BR/", "documentação, web, css",
     "A referência de HTML, CSS e JavaScript que vale mais que qualquer tutorial."),
    ("Can I use", "https://caniuse.com/", "ferramenta, css, compatibilidade",
     "Se aquele recurso de CSS já pode ser usado sem medo, e em quais navegadores."),
    ("CSS-Tricks", "https://css-tricks.com/", "artigo, css, front-end",
     "Guias de flexbox e grid que salvam qualquer layout travado."),
    ("Refactoring UI", "https://www.refactoringui.com/", "design, interface, livro",
     "Regras práticas de design de interface para quem programa e não é designer."),
    ("Laws of UX", "https://lawsofux.com/pt-br/", "design, ux, referência",
     "Os princípios de usabilidade explicados em uma página cada."),
    ("Type Scale", "https://typescale.com/", "ferramenta, tipografia, design",
     "Monta a escala tipográfica do projeto e já entrega o CSS."),
    ("Coolors", "https://coolors.co/", "ferramenta, cor, design",
     "Gerador de paletas rápido, com checagem de contraste."),
    ("Real Python", "https://realpython.com/", "tutorial, python",
     "Artigos longos e bem feitos sobre Python, do básico ao avançado."),
    ("PEP 8", "https://peps.python.org/pep-0008/", "documentação, python, estilo",
     "O guia de estilo do Python, a fonte de toda discussão sobre formatação."),
    ("Conventional Commits", "https://www.conventionalcommits.org/pt-br/", "documentação, git, processo",
     "A convenção de mensagem de commit que deixa o histórico legível."),
    ("Oh Shit, Git!?!", "https://ohshitgit.com/pt_BR/", "git, referência, socorro",
     "Como sair das enrascadas mais comuns do Git, em linguagem direta."),
    ("Regex101", "https://regex101.com/", "ferramenta, regex, código",
     "Testa expressões regulares explicando cada parte do casamento."),
    ("Excalidraw", "https://excalidraw.com/", "ferramenta, diagrama, croqui",
     "Diagramas com cara de rascunho à mão, ótimos para explicar arquitetura."),
    ("tldraw", "https://www.tldraw.com/", "ferramenta, diagrama, desenho",
     "Quadro branco infinito, rápido, para pensar desenhando."),
    ("Squoosh", "https://squoosh.app/", "ferramenta, imagem, otimização",
     "Comprime imagem no navegador comparando antes e depois lado a lado."),
    ("SVGOMG", "https://jakearchibald.github.io/svgomg/", "ferramenta, svg, otimização",
     "Limpa SVG exportado do Illustrator sem quebrar o desenho."),
    ("ArchDaily Brasil", "https://www.archdaily.com.br/", "arquitetura, referência, projeto",
     "Projetos publicados com plantas e memorial, bom banco de referência."),
    ("Dezeen", "https://www.dezeen.com/", "arquitetura, design, referência",
     "Arquitetura e design contemporâneos, com curadoria forte."),
    ("Tabelas SINAPI (Caixa)", "https://www.caixa.gov.br/site/paginas/downloads.aspx", "arquitetura, orçamento, tabela",
     "Tabela de referência de preços para orçamento de obra."),
    ("Hugging Face", "https://huggingface.co/", "ia, modelos, ferramenta",
     "Modelos abertos, conjuntos de dados e demonstrações para testar."),
    ("Papers with Code", "https://paperswithcode.com/", "ia, pesquisa, artigo",
     "Artigos de aprendizado de máquina com a implementação ao lado."),
    ("Blog do Simon Willison", "https://simonwillison.net/", "ia, blog, leitura",
     "Acompanhamento diário e cético do que acontece em IA aplicada."),
    ("Have I Been Pwned", "https://haveibeenpwned.com/", "segurança, senha, ferramenta",
     "Checa se um e-mail apareceu em vazamento de dados."),
    ("Documentação do Caddy", "https://caddyserver.com/docs/", "documentação, servidor, implantação",
     "Servidor web com HTTPS automático, usado para publicar este tipo de site."),
]

DADOS = {'prompts': PROMPTS, 'ideias': IDEIAS, 'links': LINKS}
MODELOS = {'prompts': Prompt, 'ideias': Ideia, 'links': Link}


class Command(BaseCommand):
    help = 'Cria itens de exemplo nas três áreas. Use --limpar para removê-los.'

    def add_arguments(self, parser):
        parser.add_argument('--limpar', action='store_true', help='Remove os itens de exemplo em vez de criá-los.')
        parser.add_argument('--usuario', help='A quem atribuir os itens. Padrão: o primeiro usuário do banco.')

    def handle(self, *args, **opcoes):
        self.quieto = opcoes['verbosity'] == 0
        if opcoes['limpar']:
            return self._limpar()
        self._criar(self._autor(opcoes['usuario']))

    def _contar(self, recado):
        if not self.quieto:
            self.stdout.write(self.style.SUCCESS(recado))

    def _autor(self, nome):
        """Quem aparece como 'criado por' nos itens."""
        usuarios = get_user_model().objects
        if nome:
            autor = usuarios.filter(username=nome).first()
            if not autor:
                raise CommandError(f'Não existe usuário "{nome}".')
            return autor
        autor = usuarios.order_by('id').first()
        if not autor:
            raise CommandError('Crie um usuário antes: python manage.py createsuperuser')
        return autor

    def _criar(self, autor):
        novos = {
            'prompts': self._semear(Prompt, autor, [
                dict(titulo=titulo, categoria=categoria, ferramenta=ferramenta, etiquetas=etiquetas,
                     favorito=favorito, descricao=descricao, texto=texto)
                for titulo, categoria, ferramenta, etiquetas, favorito, descricao, texto in PROMPTS
            ]),
            'ideias': self._semear(Ideia, autor, [
                dict(titulo=titulo, status=status, etiquetas=etiquetas, descricao=descricao)
                for titulo, status, etiquetas, descricao in IDEIAS
            ]),
            'links': self._semear(Link, autor, [
                dict(titulo=titulo, url=url, etiquetas=etiquetas, descricao=descricao)
                for titulo, url, etiquetas, descricao in LINKS
            ]),
        }
        for area, quantos in novos.items():
            ja_tinha = len(DADOS[area]) - quantos
            recado = f'{area}: {quantos} criados'
            if ja_tinha:
                recado += f', {ja_tinha} já existiam'
            self._contar(recado)

    def _semear(self, modelo, autor, itens):
        """Cria o que falta, pelo título. Item já existente não é tocado, nem se você o editou."""
        criados = 0
        for campos in itens:
            _, novo = modelo.objects.get_or_create(
                titulo=campos.pop('titulo'), defaults={'criado_por': autor, **campos}
            )
            criados += novo
        return criados

    def _limpar(self):
        for area, modelo in MODELOS.items():
            apagados, _ = modelo.objects.filter(titulo__in=[d[0] for d in DADOS[area]]).delete()
            self._contar(f'{area}: {apagados} removidos')

