/* Movimento do site: letras que ligam, brilho nos cartões, avisos, chip que esquenta (Circuito)
   e praça viva com árvores que reagem ao cursor (Paisagismo). */
(function () {
  'use strict';

  var reduzir = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var body = document.body;
  /* constantes do Paisagismo: precisam existir antes do return que encerra o script mais abaixo */
  var NS = 'http://www.w3.org/2000/svg';
  var CORES_FOLHA = ['#8fbf4a', '#b5d15c', '#d9c24a', '#a67c3d', '#6fa04a'];
  var passarosNoAr = 0;

  /* 1. Título que "liga" letra por letra (o texto continua legível sem JavaScript) */
  document.querySelectorAll('[data-letras]').forEach(function (el) {
    var texto = el.textContent.trim();
    el.setAttribute('aria-label', texto);
    el.textContent = '';
    Array.from(texto).forEach(function (ch, i) {
      var s = document.createElement('span');
      s.className = 'letra';
      s.setAttribute('aria-hidden', 'true');
      s.style.setProperty('--i', i);
      s.textContent = ch === ' ' ? ' ' : ch;
      el.appendChild(s);
    });
  });

  /* 2. Brilho que segue o mouse dentro dos cartões */
  document.addEventListener('pointermove', function (e) {
    var c = e.target.closest && e.target.closest('.cartao');
    if (!c) return;
    var r = c.getBoundingClientRect();
    c.style.setProperty('--mx', (e.clientX - r.left) + 'px');
    c.style.setProperty('--my', (e.clientY - r.top) + 'px');
  }, { passive: true });

  /* 3b. Botões "Copiar": copiam o texto e mostram a mensagem "Copiado" */
  function copiarTexto(texto) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(texto);
    return new Promise(function (ok, erro) {  // alternativa para páginas sem HTTPS
      var t = document.createElement('textarea');
      t.value = texto;
      t.setAttribute('readonly', '');
      t.style.cssText = 'position:fixed;opacity:0;top:0;left:0';
      document.body.appendChild(t);
      t.select();
      var deu = false;
      try { deu = document.execCommand('copy'); } catch (e) { /* segue para o erro */ }
      t.remove();
      if (deu) ok(); else erro();
    });
  }
  function aviso(mensagem) {
    var antigo = document.querySelector('.toast');
    if (antigo) antigo.remove();
    var t = document.createElement('div');
    t.className = 'toast';
    t.setAttribute('role', 'status');
    t.textContent = mensagem;
    document.body.appendChild(t);
    setTimeout(function () { t.classList.add('saindo'); }, 1500);
    setTimeout(function () { t.remove(); }, 1950);
  }
  document.addEventListener('click', function (e) {
    var linha = e.target.closest && e.target.closest('.linha-prompt');
    var endereco = linha && linha.getAttribute('data-url');
    if (endereco && !e.target.closest('a, button')) {  // links: clicar na linha abre o endereço
      if (!(window.getSelection && String(window.getSelection()))) window.open(endereco, '_blank', 'noopener');
      return;
    }
    var botao = e.target.closest && e.target.closest('.btn-copiar');
    // clicar em qualquer parte da linha do prompt (menos em links e botões) também copia
    if (!botao && linha && !e.target.closest('a, button')) botao = linha.querySelector('.btn-copiar');
    if (!botao) return;
    if (window.getSelection && String(window.getSelection())) return;  // quem está selecionando texto não copia
    var alvo = botao.getAttribute('data-alvo');
    var texto = alvo ? (document.querySelector(alvo) || {}).textContent : botao.getAttribute('data-texto');
    copiarTexto(texto || '').then(function () {
      var l = botao.closest('.linha-prompt');
      if (l) {
        l.classList.remove('copiado');
        void l.offsetWidth;  // reinicia a animação se clicar de novo
        l.classList.add('copiado');
        setTimeout(function () { l.classList.remove('copiado'); }, 1000);
      }
      if (!botao.classList.contains('titulo-copiar')) {
        if (!botao._rotulo) botao._rotulo = botao.textContent;
        botao.textContent = 'Copiado!';
        botao.classList.remove('pulsou');
        void botao.offsetWidth;
        botao.classList.add('pulsou');
        clearTimeout(botao._t);
        botao._t = setTimeout(function () { botao.textContent = botao._rotulo; botao.classList.remove('pulsou'); }, 1800);
      }
      aviso('Copiado');
    }, function () { aviso('Não foi possível copiar'); });
  });
  /* 3. Avisos somem sozinhos */
  document.querySelectorAll('.aviso').forEach(function (a) {
    setTimeout(function () {
      a.classList.add('saindo');
      setTimeout(function () { a.remove(); }, 500);
    }, 5000);
  });

  if (body.classList.contains('tema-paisagismo')) { iniciarPaisagismo(); return; }
  if (body.classList.contains('tema-circuito')) { iniciarCircuito(); }

  /* ------------------------------------------------------------------ */
  /* Paisagismo: a praça (arquivo caminhos.svg) entra na página para que as árvores possam reagir */
  function iniciarPaisagismo() {
    var url = body.getAttribute('data-cena');
    if (!url || !window.fetch) return;
    fetch(url).then(function (r) { return r.text(); }).then(function (texto) {
      var cena = document.createElement('div');
      cena.id = 'cena-viva';
      cena.setAttribute('aria-hidden', 'true');
      cena.innerHTML = texto;
      var svg = cena.querySelector('svg');
      if (!svg) return;
      body.insertBefore(cena, body.firstChild);
      body.classList.add('com-cena');
      if (reduzir && svg.pauseAnimations) svg.pauseAnimations();
      arvoresQueReagem(svg);
    }).catch(function () { /* sem a cena viva, fica a imagem parada de fundo */ });
  }

  /* Quando o cursor sacode uma árvore: algumas folhas pequenas caem ao pé dela, ficam um tempo
     no chão e somem; às vezes sai um passarinho que voa devagar para longe. */
  function grupoDe(svg, id, antesDe) {
    var g = svg.querySelector('#' + id);
    if (!g) {
      g = document.createElementNS(NS, 'g');
      g.id = id;
      if (antesDe) antesDe.parentNode.insertBefore(g, antesDe); else svg.appendChild(g);
    }
    return g;
  }

  function folhasNoChao(svg, arvore, raizArvores) {
    var chao = grupoDe(svg, 'folhas', raizArvores);  // abaixo das copas, acima dos gramados
    var caixa = arvore.getBBox();
    var cx = caixa.x + caixa.width / 2, cy = caixa.y + caixa.height / 2, R = caixa.width / 2;
    var comp = Math.max(6, Math.min(12, R * 0.22));   // folha proporcional ao tamanho da árvore
    var quantas = 5 + Math.floor(Math.random() * 4);
    for (var i = 0; i < quantas; i++) {
      var ang = Math.random() * 6.2832, rho = R * (0.72 + Math.random() * 0.5);
      var fora = document.createElementNS(NS, 'g');
      fora.setAttribute('transform', 'translate(' + (cx + Math.cos(ang) * rho).toFixed(1) + ' ' +
                        (cy + Math.sin(ang) * rho).toFixed(1) + ') rotate(' + Math.floor(Math.random() * 360) + ')');
      var folha = document.createElementNS(NS, 'path');
      folha.setAttribute('class', 'folha-i');
      folha.setAttribute('d', 'M0 0C' + (comp * 0.3) + ' ' + (-comp * 0.34) + ' ' + (comp * 0.7) + ' ' + (-comp * 0.34) +
                         ' ' + comp + ' 0C' + (comp * 0.7) + ' ' + (comp * 0.34) + ' ' + (comp * 0.3) + ' ' +
                         (comp * 0.34) + ' 0 0Z');
      folha.setAttribute('fill', CORES_FOLHA[Math.floor(Math.random() * CORES_FOLHA.length)]);
      folha.setAttribute('stroke', '#1e2a1a');
      folha.setAttribute('stroke-width', '.35');
      fora.appendChild(folha);
      chao.appendChild(fora);
      var deriva = (Math.random() * 2 - 1) * comp * 2.5;
      var pouso = 'translate:' + deriva.toFixed(1) + 'px ' + (comp * 2 + Math.random() * comp * 2).toFixed(1) + 'px';
      var giro = ((Math.random() - 0.5) * 200).toFixed(0) + 'deg';
      var anim = folha.animate([
        { opacity: 0, scale: 0.4, translate: '0px ' + (-comp * 2).toFixed(1) + 'px', rotate: '0deg', offset: 0 },
        { opacity: 1, scale: 1, translate: pouso.slice(10), rotate: giro, offset: 0.12 },
        { opacity: 1, scale: 1, translate: pouso.slice(10), rotate: giro, offset: 0.72 },
        { opacity: 0, scale: 0.9, translate: pouso.slice(10), rotate: giro, offset: 1 }
      ], { duration: 9000 + Math.random() * 3000, easing: 'ease-out', fill: 'forwards' });
      anim.onfinish = (function (el) { return function () { el.remove(); }; })(fora);
    }
  }

  function passarinho(svg, arvore, longeX, longeY) {
    if (passarosNoAr >= 2) return;
    var fauna = grupoDe(svg, 'fauna', null);
    var caixa = arvore.getBBox();
    var cx = caixa.x + caixa.width / 2, cy = caixa.y + caixa.height / 2;
    var ang = Math.atan2(longeY, longeX) + (Math.random() - 0.5) * 0.9;   // foge do cursor
    var fora = document.createElementNS(NS, 'g');
    fora.setAttribute('transform', 'translate(' + cx.toFixed(1) + ' ' + cy.toFixed(1) + ') rotate(' +
                      (ang * 180 / Math.PI).toFixed(1) + ')');
    var dentro = document.createElementNS(NS, 'g');
    dentro.setAttribute('class', 'passaro-i');
    dentro.innerHTML =
      '<path d="M-6 0L-13 -2.6L-11.5 0L-13 2.6Z" fill="#3d3128"/>' +
      '<ellipse rx="6.2" ry="2.7" fill="#4a3a2e"/>' +
      '<circle cx="6.6" r="2.3" fill="#3d3128"/>' +
      '<path d="M8.6 -.9L11.4 0L8.6 .9Z" fill="#e0a030"/>' +
      '<ellipse class="asa" cx="0" cy="-5" rx="5.2" ry="2.6" fill="#6a5644"/>' +
      '<ellipse class="asa b" cx="0" cy="5" rx="5.2" ry="2.6" fill="#6a5644"/>';
    fora.appendChild(dentro);
    fauna.appendChild(fora);
    passarosNoAr++;
    var dist = 380 + Math.random() * 220, lado = (Math.random() - 0.5) * 90;
    var anim = dentro.animate([
      { opacity: 0, scale: 1.0, translate: '0px 0px', offset: 0 },
      { opacity: 1, scale: 1.3, translate: (dist * 0.08) + 'px ' + (lado * 0.2) + 'px', offset: 0.08 },
      { opacity: 1, scale: 1.7, translate: (dist * 0.55) + 'px ' + lado + 'px', offset: 0.55 },
      { opacity: 0, scale: 1.9, translate: dist + 'px ' + (lado * 0.5) + 'px', offset: 1 }
    ], { duration: 9500, easing: 'ease-in-out', fill: 'forwards' });
    anim.onfinish = function () { fora.remove(); passarosNoAr--; };
  }
  function arvoresQueReagem(svg) {
    var arvores = Array.prototype.slice.call(svg.querySelectorAll('.copa'));
    var centros = [], pendente = false, mx = 0, my = 0;

    function medir() {
      centros = arvores.map(function (a) {
        var r = a.getBoundingClientRect();
        return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
      });
    }
    function reagir() {
      pendente = false;
      medir();  // a posição das árvores na tela pode ter mudado (janela redimensionada, painel aberto)
      arvores.forEach(function (a, i) {
        var dx = centros[i].x - mx, dy = centros[i].y - my;
        var d = Math.hypot(dx, dy) || 1;
        var f = Math.max(0, 1 - d / 300);
        /* a árvore se afasta do cursor, como empurrada pelo vento */
        a.style.translate = (dx / d * f * 14).toFixed(2) + 'px ' + (dy / d * f * 14).toFixed(2) + 'px';
        if (f > 0.3 && !a._tocada && !reduzir) {
          a._tocada = true;
          a.classList.remove('balanca');
          void a.getBoundingClientRect();
          a.classList.add('balanca');
          folhasNoChao(svg, a, arvores[0].parentNode);
          if (Math.random() < 0.85 && performance.now() > (a._passaroAte || 0)) {
            a._passaroAte = performance.now() + 8000;
            passarinho(svg, a, dx, dy);
          }
        } else if (f < 0.1) {
          a._tocada = false;
        }
      });
    }
    arvores.forEach(function (a) {
      a.addEventListener('animationend', function (ev) {
        if (ev.animationName === 'balanca') a.classList.remove('balanca');
      });
    });
    medir();
    var t;
    window.addEventListener('resize', function () { clearTimeout(t); t = setTimeout(medir, 200); });
    window.addEventListener('pointermove', function (e) {
      mx = e.clientX; my = e.clientY;
      if (!pendente) { pendente = true; requestAnimationFrame(reagir); }
    }, { passive: true });
  }

  /* ------------------------------------------------------------------ */
  /* Circuito: placa de circuito viva. Perto do cursor o chip "esquenta": trilhas ficam laranja e
     vermelhas, brilham e depois esfriam devagar. */
  function iniciarCircuito() {
    var canvas = document.createElement('canvas');
    canvas.id = 'fundo-vivo';
    canvas.setAttribute('aria-hidden', 'true');
    var ctx = canvas.getContext('2d');
    if (!ctx) return;
    body.insertBefore(canvas, body.firstChild);
    body.classList.add('com-canvas');

    var CELL = 44;
    var DIRS = [[1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1]];
    var RAIO = 150;        // alcance do calor nas trilhas
    var RESFRIA = 0.6;     // quanto o calor some por segundo
    var MAX_EXTRAS = 24;
    var W, H, tracos = [], pulsos = [];
    var mouse = { x: -9999, y: -9999, ativo: false };
    var halo = { x: -9999, y: -9999, calor: 0 };

    function medir() {
      var dpr = Math.min(2, window.devicePixelRatio || 1);
      W = window.innerWidth;
      H = window.innerHeight;
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    /* Trilhas com curvas de 45°, como numa placa de verdade */
    function gerar() {
      tracos = [];
      pulsos = [];
      var cols = Math.ceil(W / CELL) + 1;
      var rows = Math.ceil(H / CELL) + 1;
      var n = Math.round(cols * rows / (W < 700 ? 16 : 11));
      for (var i = 0; i < n; i++) {
        var x = Math.floor(Math.random() * cols);
        var y = Math.floor(Math.random() * rows);
        var d = Math.floor(Math.random() * 8);
        var pts = [{ x: x * CELL, y: y * CELL }];
        var passos = 3 + Math.floor(Math.random() * 6);
        for (var k = 0; k < passos; k++) {
          var len = 2 + Math.floor(Math.random() * 6);
          x += DIRS[d][0] * len;
          y += DIRS[d][1] * len;
          pts.push({ x: x * CELL, y: y * CELL });
          var r = Math.random();
          if (r < 0.45) d = (d + 1) % 8; else if (r < 0.9) d = (d + 7) % 8;
        }
        var total = 0, segs = [];
        for (var j = 1; j < pts.length; j++) {
          var a = pts[j - 1], b = pts[j];
          var l = Math.hypot(b.x - a.x, b.y - a.y);
          segs.push({ a: a, b: b, l: l, ini: total, mx: (a.x + b.x) / 2, my: (a.y + b.y) / 2, h: 0 });
          total += l;
        }
        tracos.push({ pts: pts, segs: segs, total: total, hp: [0, 0] });
      }
      for (var p = 0; p < Math.round(n * 0.7); p++) pulsos.push(novoPulso());
    }

    function novoPulso(tr, pos, sentido, extra) {
      tr = tr || tracos[Math.floor(Math.random() * tracos.length)];
      sentido = sentido || (Math.random() < 0.5 ? 1 : -1);
      return {
        tr: tr,
        d: pos != null ? pos : Math.random() * tr.total,
        v: (extra ? 230 : 50 + Math.random() * 90) * sentido,
        cauda: extra ? 100 : 70,
        extra: !!extra
      };
    }

    function pontoEm(tr, d) {
      d = Math.max(0, Math.min(tr.total, d));
      for (var i = 0; i < tr.segs.length; i++) {
        var s = tr.segs[i];
        if (d <= s.ini + s.l || i === tr.segs.length - 1) {
          var t = s.l ? (d - s.ini) / s.l : 0;
          return { x: s.a.x + (s.b.x - s.a.x) * t, y: s.a.y + (s.b.y - s.a.y) * t };
        }
      }
    }

    function perto(v) { return Math.max(0, 1 - v); }

    /* ciano (frio) -> branco quente -> laranja -> vermelho (chip esquentando) */
    var ESCALA = [[0, 57, 208, 245], [0.35, 250, 232, 226], [0.7, 255, 172, 152], [1, 255, 128, 128]];
    function cor(h) {
      for (var i = 1; i < ESCALA.length; i++) {
        if (h <= ESCALA[i][0]) {
          var a = ESCALA[i - 1], b = ESCALA[i], t = (h - a[0]) / (b[0] - a[0]);
          return Math.round(a[1] + (b[1] - a[1]) * t) + ',' + Math.round(a[2] + (b[2] - a[2]) * t) + ',' +
                 Math.round(a[3] + (b[3] - a[3]) * t);
        }
      }
      return '255,128,128';
    }

    function desenhar() {
      ctx.clearRect(0, 0, W, H);
      ctx.lineCap = 'round';
      var i, j, tr, s;

      /* brilho avermelhado em volta do cursor: o "chip" esquentando */
      if (halo.calor > 0.01) {
        var g = ctx.createRadialGradient(halo.x, halo.y, 0, halo.x, halo.y, 210);
        g.addColorStop(0, 'rgba(255,140,130,' + (0.2 * halo.calor).toFixed(3) + ')');
        g.addColorStop(0.45, 'rgba(255,150,140,' + (0.08 * halo.calor).toFixed(3) + ')');
        g.addColorStop(1, 'rgba(255,150,140,0)');
        ctx.fillStyle = g;
        ctx.fillRect(halo.x - 210, halo.y - 210, 420, 420);
      }

      /* trilhas */
      for (i = 0; i < tracos.length; i++) {
        tr = tracos[i];
        for (j = 0; j < tr.segs.length; j++) {
          s = tr.segs[j];
          var h = s.h;
          ctx.strokeStyle = 'rgba(' + cor(h) + ',' + (0.15 + h * 0.6).toFixed(3) + ')';
          ctx.lineWidth = 1 + h * 0.9;
          if (h > 0.25) { ctx.shadowColor = 'rgba(255,140,130,' + (h * 0.6).toFixed(2) + ')'; ctx.shadowBlur = 9 * h; }
          ctx.beginPath();
          ctx.moveTo(s.a.x, s.a.y);
          ctx.lineTo(s.b.x, s.b.y);
          ctx.stroke();
          if (h > 0.25) ctx.shadowBlur = 0;
        }
        /* terminais (pads) nas pontas */
        var pontas = [tr.pts[0], tr.pts[tr.pts.length - 1]];
        for (j = 0; j < 2; j++) {
          var hp = tr.hp[j];
          ctx.strokeStyle = 'rgba(' + cor(hp) + ',' + (0.3 + hp * 0.5).toFixed(3) + ')';
          ctx.lineWidth = 1.2 + hp;
          if (hp > 0.25) { ctx.shadowColor = 'rgba(255,140,130,' + (hp * 0.6).toFixed(2) + ')'; ctx.shadowBlur = 8 * hp; }
          ctx.beginPath();
          ctx.arc(pontas[j].x, pontas[j].y, 3.2 + hp * 2.4, 0, 6.2832);
          ctx.stroke();
          if (hp > 0.25) ctx.shadowBlur = 0;
        }
      }

      /* pulsos de luz: os do cursor nascem quentes */
      for (i = 0; i < pulsos.length; i++) {
        var p = pulsos[i];
        if (p.d < 0 || p.d > p.tr.total) continue;
        var sinal = p.v > 0 ? 1 : -1, partes = 8;
        var corCauda = p.extra ? '255,196,184' : '160,240,255';
        for (j = 0; j < partes; j++) {
          var a = pontoEm(p.tr, p.d - sinal * (j * p.cauda / partes));
          var c = pontoEm(p.tr, p.d - sinal * ((j + 1) * p.cauda / partes));
          ctx.strokeStyle = 'rgba(' + corCauda + ',' + ((1 - j / partes) * 0.85).toFixed(3) + ')';
          ctx.lineWidth = 2.2 - j * 0.15;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(c.x, c.y);
          ctx.stroke();
        }
        var hd = pontoEm(p.tr, p.d);
        ctx.fillStyle = p.extra ? 'rgba(255,140,130,0.22)' : 'rgba(57,208,245,0.22)';
        ctx.beginPath(); ctx.arc(hd.x, hd.y, 9, 0, 6.2832); ctx.fill();
        ctx.fillStyle = p.extra ? '#fff1e0' : '#e8fbff';
        ctx.beginPath(); ctx.arc(hd.x, hd.y, 2.8, 0, 6.2832); ctx.fill();
      }
    }

    function atualizar(dt) {
      var i, j, tr, s, alvo;
      /* pulsos */
      for (i = pulsos.length - 1; i >= 0; i--) {
        var p = pulsos[i];
        p.d += p.v * dt;
        var fora = p.v > 0 ? p.d > p.tr.total + p.cauda : p.d < -p.cauda;
        if (!fora) continue;
        if (p.extra) { pulsos.splice(i, 1); continue; }
        var novo = novoPulso(null, null, Math.random() < 0.5 ? 1 : -1);
        novo.d = novo.v > 0 ? -novo.cauda : novo.tr.total + novo.cauda;
        pulsos[i] = novo;
      }
      /* calor: sobe perto do cursor e esfria devagar depois que ele sai */
      for (i = 0; i < tracos.length; i++) {
        tr = tracos[i];
        for (j = 0; j < tr.segs.length; j++) {
          s = tr.segs[j];
          alvo = mouse.ativo ? perto(Math.hypot(mouse.x - s.mx, mouse.y - s.my) / RAIO) : 0;
          s.h = Math.max(alvo, s.h - dt * RESFRIA);
        }
        for (j = 0; j < 2; j++) {
          var pt = tr.pts[j === 0 ? 0 : tr.pts.length - 1];
          alvo = mouse.ativo ? perto(Math.hypot(mouse.x - pt.x, mouse.y - pt.y) / (RAIO * 0.75)) : 0;
          tr.hp[j] = Math.max(alvo, tr.hp[j] - dt * RESFRIA);
        }
      }
      /* halo suavizado */
      halo.x += (mouse.x - halo.x) * Math.min(1, dt * 8);
      halo.y += (mouse.y - halo.y) * Math.min(1, dt * 8);
      halo.calor += ((mouse.ativo ? 1 : 0) - halo.calor) * Math.min(1, dt * 2.5);
    }

    /* Cursor: acha a trilha mais próxima e solta um pulso quente nela */
    function distSeg(px, py, s) {
      var dx = s.b.x - s.a.x, dy = s.b.y - s.a.y;
      var t = Math.max(0, Math.min(1, ((px - s.a.x) * dx + (py - s.a.y) * dy) / (dx * dx + dy * dy)));
      return { dist: Math.hypot(px - (s.a.x + dx * t), py - (s.a.y + dy * t)), t: t };
    }

    var ultimo = 0;
    window.addEventListener('pointermove', function (e) {
      if (!mouse.ativo && halo.calor < 0.02) { halo.x = e.clientX; halo.y = e.clientY; }
      mouse.x = e.clientX; mouse.y = e.clientY; mouse.ativo = true;
      var agora = performance.now();
      if (reduzir || agora - ultimo < 110) return;
      ultimo = agora;
      var extras = 0, i, j;
      for (i = 0; i < pulsos.length; i++) if (pulsos[i].extra) extras++;
      if (extras >= MAX_EXTRAS) return;
      var melhor = null;
      for (i = 0; i < tracos.length; i++) {
        for (j = 0; j < tracos[i].segs.length; j++) {
          var r = distSeg(mouse.x, mouse.y, tracos[i].segs[j]);
          if (r.dist < 70 && (!melhor || r.dist < melhor.dist)) {
            melhor = { dist: r.dist, tr: tracos[i], pos: tracos[i].segs[j].ini + tracos[i].segs[j].l * r.t };
          }
        }
      }
      if (melhor) pulsos.push(novoPulso(melhor.tr, melhor.pos, Math.random() < 0.5 ? 1 : -1, true));
    }, { passive: true });
    document.documentElement.addEventListener('pointerleave', function () { mouse.ativo = false; });

    var antes = 0, quadro = null, timer = null;
    function ciclo(t) {
      var dt = Math.min(0.05, (t - antes) / 1000 || 0);
      antes = t;
      atualizar(dt);
      desenhar();
      quadro = requestAnimationFrame(ciclo);
    }

    function iniciar() {
      if (quadro) cancelAnimationFrame(quadro);
      medir();
      gerar();
      if (reduzir) { desenhar(); return; }
      antes = performance.now();
      quadro = requestAnimationFrame(ciclo);
    }

    window.addEventListener('resize', function () {
      clearTimeout(timer);
      timer = setTimeout(iniciar, 200);
    });

    iniciar();
  }
})();
