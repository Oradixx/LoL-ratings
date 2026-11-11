/* Rift Scout — classement, fiche joueur, scouting. Données : window.DATA (voir pipeline/build.py). */
(function () {
  'use strict';
  const D = window.DATA;
  const ROLES = ['Top', 'Jungle', 'Mid', 'ADC', 'Support'];
  const FAC = D.facets;
  const FLABEL = { lane: 'Phase de lane', early: 'Début de partie', fight: 'Teamfight', carry: 'Dégâts', eco: 'Farm et or', vision: 'Vision', safe: 'Survie', obj: 'Objectifs' };
  const FSHORT = { lane: 'Lane', early: 'Début', fight: 'TF', carry: 'Dég.', eco: 'Or', vision: 'Vis.', safe: 'Surv.', obj: 'Obj.' };
  const FSAY = {
    lane: 'gagne sa lane (or, XP et sbires à 15 min)', early: 'pèse dans les 15 premières minutes', fight: 'présent et efficace dans les combats',
    carry: 'gros dégâts pour son poste', eco: 'farm et revenus élevés', vision: 'contrôle de la vision', safe: 'meurt peu', obj: 'son équipe prend les objectifs neutres'
  };
  const FLOW = {
    lane: 'souvent en retard à 15 min', early: 'peu d\'impact en début de partie', fight: 'moins présent dans les combats', carry: 'peu de dégâts pour son poste',
    eco: 'farm et revenus en retrait', vision: 'vision en retrait', safe: 'meurt beaucoup', obj: 'son équipe cède les objectifs neutres'
  };
  const TIERS = D.tiers;
  const ROLE_PL = { Top: 'tops', Jungle: 'junglers', Mid: 'mids', ADC: 'ADC', Support: 'supports' };
  const TIER_OF = ['de ligue majeure', 'de deuxième niveau', 'de troisième niveau'];
  const $ = (s, el) => (el || document).querySelector(s);
  const h = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const fmt = (x, d) => (x == null ? '–' : Number(x).toLocaleString('fr-FR', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 }));
  const pctTxt = (x) => (x == null ? '–' : fmt(x * 100, 0) + ' %');
  const lgName = (l) => D.pretty[l] || l;
  const nInt = (x) => Math.round(x);

  const state = { season: Object.keys(D.seasons).sort().pop(), view: 'rank', role: '', tier: '0', region: '', league: '', event: '', minG: 15, q: '', shown: 100,
    sc: { tid: null, role: 'Mid', tier: '', region: '', league: '', minNote: 0, minG: 20, sort: 'score', shown: 60, ref: null, reach: true } };
  let S, byId, med;

  function load() {
    S = D.seasons[state.season];
    byId = new Map(S.players.map((p) => [p.id, p]));
    med = {};
    for (const p of S.players) { const k = p.role + p.tier; (med[k] = med[k] || []).push(p); }
    for (const k in med) {
      const arr = med[k]; const m = FAC.map((_, i) => median(arr.map((p) => p.f[i]).filter((v) => v != null)));
      med[k] = { f: m, note: median(arr.map((p) => p.note)) };
    }
  }
  function median(a) { if (!a.length) return null; a = a.slice().sort((x, y) => x - y); const m = a.length >> 1; return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2; }

  /* couleur d'une note : du gris au cobalt, or au-dessus de 90 */
  function noteVar(n) { return n >= 90 ? 'var(--n4)' : n >= 82 ? 'var(--n3)' : n >= 72 ? 'var(--n2)' : n >= 60 ? 'var(--n1)' : 'var(--n0)'; }
  function noteCls(n) { return n >= 90 ? 't-gold' : n >= 80 ? 't-cob' : n >= 60 ? 't-mid' : 't-low'; }
  function strip(p) {
    return '<span class="strip" aria-hidden="true">' + p.f.map((v, i) => {
      if (v == null) return '<i style="height:3px;background:var(--line)"></i>';
      const hgt = Math.max(16, Math.min(100, 58 + (v - p.note) * 5.5)); // hauteur : écart à sa propre note, pour lire la forme du profil
      return `<i title="${FLABEL[FAC[i]]} : ${nInt(v)}" style="height:${hgt}%;background:${noteVar(v)}"></i>`;
    }).join('') + '</span>';
  }
  function evNote(p, ev) { const e = p.ev.find((x) => x.e === ev); return e || null; }

  /* ------------------------------------------------------------ style de jeu */
  // indices du vecteur s : 0 or, 1 dégâts, 2 part des kills, 3 kills+assists à 15, 4 participation à 15, 5 morts, 6 dégâts subis, 7 vision, 8 farm, 9 champions carry, 10 champions tank
  const ARCH = {
    Top: [['Carry de side lane', [0, 1, 9], []], ['Tank de première ligne', [6, 10], [1]], ['Weakside solide', [], [0, 5, 4]], ['Bagarreur de début de partie', [3, 4, 2], []]],
    Jungle: [['Jungler carry', [0, 1, 8], []], ['Facilitateur', [7, 4], [0]], ['Agresseur précoce', [3, 2], []], ['Jungler de première ligne', [6, 10], [1]]],
    Mid: [['Carry principal', [0, 1, 2], []], ['Contrôle et farm', [8], [5, 3]], ['Faiseur de jeu', [3, 4], [8]], ['Mid utilitaire', [7], [0, 1]]],
    ADC: [['Hypercarry', [0, 1, 8], []], ['Agressif en lane', [3, 2, 4], []], ['Sûr, tourné vers la fin de partie', [8], [5, 3]], ['ADC utilitaire', [7], [0, 1]]],
    Support: [['Engage, première ligne', [6, 10], []], ['Protecteur', [], [6, 10, 5]], ['Faiseur de jeu', [3, 4], []], ['Contrôle de vision', [7], [3]]]
  };
  function archetype(p) {
    if (!p.s) return null;
    let best = null, bv = 0.45;
    for (const [name, plus, minus] of ARCH[p.role]) {
      const v = (plus.reduce((a, i) => a + p.s[i], 0) - minus.reduce((a, i) => a + p.s[i], 0)) / (plus.length + minus.length);
      if (v > bv) { bv = v; best = name; }
    }
    return best || 'Profil équilibré';
  }
  function styleDist2(a, b) { let d = 0; for (let i = 0; i < a.s.length; i++) { const x = a.s[i] - b.s[i]; d += x * x; } return d; }
  function similarity(a, b) { if (!a.s || !b.s) return null; return 100 * Math.exp(-styleDist2(a, b) / 18); }

  /* ------------------------------------------------------------ forces / faiblesses */
  function insights(p) {
    const plus = [], minus = [], w = D.weights[p.role];
    const grp = ROLE_PL[p.role] + ' ' + TIER_OF[p.tier];
    const idx = FAC.map((f, i) => i).filter((i) => p.fp[i] != null && (w[FAC[i]] > 0 || FAC[i] === 'obj'));
    idx.slice().sort((a, b) => p.fp[b] - p.fp[a]).slice(0, 3).forEach((i) => {
      if (p.fp[i] >= 0.7) plus.push(`<b>${FLABEL[FAC[i]]}</b> : ${FSAY[FAC[i]]} (${topTxt(p.fp[i])} des ${grp})`);
    });
    idx.slice().sort((a, b) => p.fp[a] - p.fp[b]).slice(0, 2).forEach((i) => {
      if (p.fp[i] <= 0.3) minus.push(`<b>${FLABEL[FAC[i]]}</b> : ${FLOW[FAC[i]]} (${nInt(p.f[i])}, pour une note générale de ${nInt(p.note)})`);
    });
    if (p.weak != null && p.strong != null) {
      if (p.weak_pc >= 0.75 && p.weak_pc >= p.strong_pc) plus.push(`<b>Weakside</b> : tient sa lane quand son équipe joue ailleurs (${topTxt(p.weak_pc)})`);
      if (p.strong_pc >= 0.75 && p.strong_pc > p.weak_pc) plus.push(`<b>Strongside</b> : convertit l'aide reçue en avance et en dégâts (${topTxt(p.strong_pc)})`);
      if (p.weak_pc <= 0.25) minus.push('<b>Weakside</b> : souffre quand son équipe joue ailleurs');
      if (p.strong_pc <= 0.25) minus.push('<b>Strongside</b> : convertit peu l\'aide reçue');
    }
    if (p.clutch != null && p.clutch >= 1) plus.push(`<b>Grands matchs</b> : meilleur en playoffs et à l'international qu'en saison régulière (${p.big_n} parties)`);
    if (p.clutch != null && p.clutch <= -1) minus.push(`<b>Grands matchs</b> : en dessous de son niveau habituel en playoffs et à l'international (${p.big_n} parties)`);
    if (p.reg != null && p.reg >= 0.8) plus.push('<b>Régularité</b> : niveau très stable d\'une partie à l\'autre');
    if (p.reg != null && p.reg <= 0.15) minus.push('<b>Régularité</b> : niveau très variable d\'une partie à l\'autre');
    if (p.pool != null && p.pool >= 0.85) plus.push(`<b>Pool de champions</b> : large (${p.pool_n} champions joués)`);
    if (p.pool != null && p.pool <= 0.12) minus.push(`<b>Pool de champions</b> : étroit (${p.pool_n} champions joués)`);
    return { plus, minus };
  }
  function topTxt(pc) { const t = Math.max(1, Math.round((1 - pc) * 100)); return t <= 50 ? `top ${t} %` : `${t}e centile`; }

  /* ------------------------------------------------------------ classement */
  function filtered(ignoreRole) {
    const q = state.q.trim().toLowerCase();
    let L = S.players.filter((p) =>
      (ignoreRole || !state.role || p.role === state.role) &&
      (q || state.tier === '' || p.tier === +state.tier) &&
      (!state.region || p.region === state.region) &&
      (!state.league || p.league === state.league) &&
      (q || p.n >= state.minG) &&
      (!q || p.name.toLowerCase().includes(q) || p.team.toLowerCase().includes(q)));
    if (state.event) {
      L = L.map((p) => ({ p, e: evNote(p, state.event) })).filter((x) => x.e).sort((a, b) => b.e.note - a.e.note);
      return L.map((x) => Object.assign({ _e: x.e }, x.p));
    }
    return L;
  }
  function scopeLabel() {
    const parts = [];
    if (state.event) parts.push(state.event);
    else if (state.league) parts.push(lgName(state.league));
    else if (state.region) parts.push(state.region);
    else if (state.tier !== '') parts.push(['ligues majeures', 'deuxième niveau', 'troisième niveau'][+state.tier]);
    else parts.push('toutes ligues');
    return parts.join(', ');
  }
  function renderFive() {
    const L = filtered(true);
    const el = $('#five'); let html = '';
    for (const r of ROLES) {
      const p = L.find((x) => x.role === r);
      if (!p) { html += `<button disabled><span class="role">${r}</span><span class="empty">Aucun joueur</span></button>`; continue; }
      const n = p._e ? p._e.note : p.note;
      html += `<button data-p="${p.id}"><span class="role">${r}</span><span class="name">${h(p.name)}</span><span class="num note ${noteCls(n)}">${nInt(n)}</span><span class="team">${h(p._e ? p._e.team : p.team)}</span></button>`;
    }
    el.innerHTML = html;
    $('#five-title').textContent = 'Le meilleur cinq, ' + scopeLabel();
    $('#five-sub').textContent = `Saison ${state.season} : ${fmt(S.games)} parties, du ${frDate(S.from)} au ${frDate(S.to)}. Chaque joueur est noté de 1 à 100 sur la même échelle, quelle que soit sa ligue.`;
  }
  function frDate(d) { return new Date(d + 'T12:00:00').toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' }); }
  function renderRank() {
    renderFive();
    const L = filtered(false);
    const el = $('#rows');
    $('#count').textContent = L.length ? `${fmt(L.length)} joueur${L.length > 1 ? 's' : ''}` : '';
    if (!L.length) { el.innerHTML = '<p class="none">Aucun joueur ne correspond à ces filtres. Élargissez le niveau de ligue ou baissez le nombre minimum de parties.</p>'; return; }
    let html = '';
    L.slice(0, state.shown).forEach((p, i) => {
      const n = p._e ? p._e.note : p.note;
      const d = p._e ? p._e.note - p.note : p.form - p.note;
      const tc = d >= 1.5 ? 'up' : d <= -1.5 ? 'down' : 'flat';
      html += `<button class="row" data-p="${p.id}"><span class="rank">${i + 1}</span><span class="num note ${noteCls(n)}">${nInt(n)}</span>
        <span class="who"><b>${h(p.name)}</b><small>${h(p._e ? p._e.team : p.team)}, ${h(lgName(p.league))}</small></span>
        <span class="pos">${p.role}</span>${strip(p)}
        <span class="trend ${tc} r trend-cell" title="${p._e ? 'Écart avec sa note de saison' : 'Forme : 15 dernières parties par rapport à la saison'}">${d > 0 ? '+' : ''}${fmt(d, 1)}</span>
        <span class="r games">${p._e ? p._e.n : p.n}</span></button>`;
    });
    if (L.length > state.shown) html += `<button class="more" id="more">Afficher 100 joueurs de plus</button>`;
    el.innerHTML = html;
    $('#th-trend').textContent = state.event ? 'Écart saison' : 'Forme';
  }
  function fillSelects() {
    const leagues = {}, regions = new Set(), events = {};
    for (const p of S.players) {
      leagues[p.league] = p.tier; regions.add(p.region);
      for (const e of p.ev) events[e.e] = (events[e.e] || { n: 0, cup: e.cup, d: e.d }), events[e.e].n++, events[e.e].d = e.d > events[e.e].d ? e.d : events[e.e].d;
    }
    const lgOpts = (sel) => '<option value="">Toutes</option>' + [0, 1, 2].map((t) => `<optgroup label="${TIERS[t]}">` +
      Object.keys(leagues).filter((l) => leagues[l] === t).sort((a, b) => (S.leagues[b] || 0) - (S.leagues[a] || 0))
        .map((l) => `<option value="${h(l)}"${l === sel ? ' selected' : ''}>${h(lgName(l))}${D.desc[l] && lgName(l) === l ? ' (' + h(D.desc[l]) + ')' : ''}</option>`).join('') + '</optgroup>').join('');
    const rgOpts = (sel) => '<option value="">Toutes</option>' + [...regions].sort().map((r) => `<option${r === sel ? ' selected' : ''}>${h(r)}</option>`).join('');
    $('#f-league').innerHTML = lgOpts(state.league); $('#f-region').innerHTML = rgOpts(state.region);
    $('#s-league').innerHTML = lgOpts(state.sc.league); $('#s-region').innerHTML = rgOpts(state.sc.region);
    const evs = Object.keys(events).filter((e) => events[e].n >= 20);
    const grp = (cup) => evs.filter((e) => events[e].cup === cup).sort((a, b) => (cup ? events[b].n - events[a].n : a.localeCompare(b)));
    $('#f-event').innerHTML = '<option value="">Saison entière</option><optgroup label="Tournois internationaux et coupes">' + grp(true).map((e) => `<option${e === state.event ? ' selected' : ''}>${h(e)}</option>`).join('') +
      '</optgroup><optgroup label="Ligues, par segment">' + grp(false).map((e) => `<option${e === state.event ? ' selected' : ''}>${h(e)}</option>`).join('') + '</optgroup>';
    if (state.event && !events[state.event]) state.event = '';
  }

  /* ------------------------------------------------------------ fiche joueur */
  function rail(label, v, pc, ref, cmp) {
    if (v == null) return '';
    const x = (n) => Math.max(0, Math.min(100, (n - 30) / 69 * 100));
    return `<div class="rail"><span>${label}</span><span class="bar"><i style="width:${x(v)}%;background:${noteVar(v)}"></i>${ref != null ? `<u style="left:${x(ref)}%"></u>` : ''}${cmp != null ? `<s style="left:${x(cmp)}%"></s>` : ''}</span><b class="${noteCls(v)}">${nInt(v)}</b><small>${pc != null ? topTxt(pc) : ''}</small></div>`;
  }
  function openSheet(id, cmpId) {
    const p = byId.get(id); if (!p) return;
    const cmp = cmpId && cmpId !== id ? byId.get(cmpId) : null;
    const m = med[p.role + p.tier]; const ins = insights(p); const arch = archetype(p);
    const grp = ROLE_PL[p.role] + ' ' + TIER_OF[p.tier];
    const rankIn = S.players.filter((x) => x.role === p.role && x.tier === p.tier && x.n >= 15 && x.note > p.note).length + 1;
    const d = p.form - p.note;
    let html = `<header><span class="num note ${noteCls(p.note)}">${nInt(p.note)}</span><div><h2 id="sheet-name">${h(p.name)}</h2>
      <p class="meta">${p.role}, ${h(p.team)}, ${h(lgName(p.league))} (${h(p.region)})<br>${rankIn}<sup>${rankIn === 1 ? 'er' : 'e'}</sup> des ${grp}, saison ${state.season}</p></div><button class="close" data-close>Fermer</button></header>`;
    html += `<section><div class="split">
      <div><small>Niveau de son équipe</small><span class="num">${nInt(p.team_lvl)}</span></div>
      <div><small>Écart individuel</small><span class="num ${p.ind >= 0 ? 'up' : 'down'}">${p.ind >= 0 ? '+' : ''}${fmt(p.note - p.team_lvl, 1)}</span></div>
      <div><small>Forme, 15 dernières parties</small><span class="num ${d >= 1.5 ? 'up' : d <= -1.5 ? 'down' : ''}">${nInt(p.form)}</span></div>
      <div><small>Parties jouées, ${pctTxt(p.st.win)} de victoires</small><span class="num">${p.n}</span></div></div>
      <div class="tags">${arch ? `<span class="tag gold">${arch}</span>` : ''}${styleTags(p).map((t) => `<span class="tag">${t}</span>`).join('')}</div></section>`;
    if (ins.plus.length || ins.minus.length) html += `<section><div class="two"><div><h3>Forces</h3>${ins.plus.length ? `<ul class="say">${ins.plus.map((x) => `<li>${x}</li>`).join('')}</ul>` : '<p class="legend">Rien qui ressorte nettement par rapport à son poste.</p>'}</div>
      <div><h3>Points faibles</h3>${ins.minus.length ? `<ul class="say minus">${ins.minus.map((x) => `<li>${x}</li>`).join('')}</ul>` : '<p class="legend">Aucun point faible marqué par rapport à son poste.</p>'}</div></div></section>`;
    html += `<section><h3>Profil par facette</h3>` + FAC.map((f, i) => rail(FLABEL[f], p.f[i], p.fp[i], m.f[i], cmp && cmp.role === p.role ? cmp.f[i] : null)).join('') +
      (p.weak != null ? rail('Weakside', p.weak, p.weak_pc, null, cmp ? cmp.weak : null) : '') + (p.strong != null ? rail('Strongside', p.strong, p.strong_pc, null, cmp ? cmp.strong : null) : '') +
      `<p class="legend">Trait noir : médiane des ${grp}. ${cmp && cmp.role === p.role ? `Cadre rouge : ${h(cmp.name)} (${nInt(cmp.note)}). ` : ''}Le classement à droite compare aux ${grp}.</p></section>`;
    if (p.ev.length) html += `<section><h3>Note par événement</h3><div class="events">` + p.ev.map((e) =>
      `<div class="ev"><span>${h(e.e)}</span><span class="rail" style="display:block;padding:0"><span class="bar" style="display:block"><i style="width:${Math.max(0, (e.note - 30) / 69 * 100)}%;background:${noteVar(e.note)}"></i><u style="left:${(p.note - 30) / 69 * 100}%"></u></span></span><b class="num ${noteCls(e.note)}" style="font-size:22px;text-align:right">${nInt(e.note)}</b><small>${e.n} parties, ${pctTxt(e.w)} vict.</small></div>`).join('') +
      `</div><p class="legend">Trait noir : sa note sur la saison. Un événement de quelques parties est ramené vers la note de saison.</p></section>`;
    const st = p.st;
    html += `<section><h3>Statistiques moyennes</h3><div class="stats">
      <div><small>KDA</small><b>${fmt(st.kda, 2)}</b></div><div><small>Participation aux kills</small><b>${pctTxt(st.kp)}</b></div>
      <div><small>Dégâts par minute</small><b>${fmt(st.dpm)}</b></div><div><small>Part des dégâts</small><b>${pctTxt(st.dsh)}</b></div>
      <div><small>Écart d'or à 15 min</small><b>${st.gd15 > 0 ? '+' : ''}${fmt(st.gd15)}</b></div><div><small>Écart de sbires à 15 min</small><b>${st.cd15 > 0 ? '+' : ''}${fmt(st.cd15, 1)}</b></div>
      <div><small>Écart d'XP à 15 min</small><b>${st.xd15 > 0 ? '+' : ''}${fmt(st.xd15)}</b></div><div><small>Part de l'or</small><b>${pctTxt(st.gsh)}</b></div>
      <div><small>Sbires par minute</small><b>${fmt(st.cspm, 1)}</b></div><div><small>Vision par minute</small><b>${fmt(st.vspm, 2)}</b></div>
      <div><small>Morts par partie</small><b>${fmt(st.dpg, 1)}</b></div><div><small>Premier sang (kill ou assist)</small><b>${pctTxt(st.fb)}</b></div></div></section>`;
    if (p.ch.length) html += `<section><h3>Champions les plus joués</h3><div class="champs">${p.ch.map((c) => `<span>${h(c[0])} <small>${c[1]} parties, ${pctTxt(c[2])}</small></span>`).join('')}</div></section>`;
    if (p.s) {
      const sims = S.players.filter((x) => x.role === p.role && x.id !== p.id && x.s && x.n >= 15 && x.note >= p.note - 20).map((x) => [similarity(p, x), x]).sort((a, b) => b[0] - a[0]).slice(0, 6);
      html += `<section><h3>Joueurs au style le plus proche</h3><div class="simlist">${sims.map(([s, x]) => `<button data-p="${x.id}"><span class="num ${noteCls(x.note)}">${nInt(x.note)}</span><span>${h(x.name)} <small>${h(x.team)}, ${h(lgName(x.league))}</small></span><small>${fmt(s)} % de similarité</small></button>`).join('')}</div>
        <p style="margin-top:14px"><button class="cta" data-scout="${p.id}">Chercher un remplaçant à ${h(p.name)}</button></p></section>`;
    }
    $('#sheet').innerHTML = html; $('#sheet').scrollTop = 0;
    $('#sheet-wrap').classList.add('open'); $('#sheet').focus();
  }
  function styleTags(p) {
    if (!p.s) return [];
    const T = [[0, 'Beaucoup de ressources', 'Peu de ressources'], [3, 'Actif avant 15 min', 'Discret avant 15 min'], [5, 'Prend des risques', 'Joue la sécurité'],
      [7, 'Investit dans la vision', null], [8, 'Gros farmeur', null], [6, 'Encaisse pour l\'équipe', null]];
    const out = [];
    for (const [i, hi, lo] of T) { if (p.s[i] >= 1 && hi) out.push(hi); else if (p.s[i] <= -1 && lo) out.push(lo); }
    return out.slice(0, 4);
  }
  function closeSheet() { $('#sheet-wrap').classList.remove('open'); }

  /* ------------------------------------------------------------ scouting */
  function team(tid) { return S.teams.find((t) => t.tid === tid); }
  function setTeam(tid) { state.sc.tid = tid; state.sc.ref = null; const t = team(tid); if (t && !t.roster[state.sc.role]) state.sc.role = ROLES.find((r) => t.roster[r]) || 'Mid'; state.sc.shown = 60; renderScout(); }
  function teamNeeds(t, role) {
    const others = ROLES.filter((r) => r !== role).map((r) => byId.get(t.roster[r])).filter(Boolean);
    if (!others.length) return null;
    const avgNote = others.reduce((a, p) => a + p.note, 0) / others.length;
    const fac = FAC.map((f, i) => { const v = others.map((p) => p.f[i]).filter((x) => x != null); return v.length ? v.reduce((a, b) => a + b, 0) / v.length : avgNote; });
    const gap = fac.map((v, i) => (FAC[i] === 'obj' ? 0 : Math.max(0, avgNote - v)));
    const gold = others.reduce((a, p) => a + (p.s ? p.s[0] : 0), 0);
    return { others, avgNote, fac, gap, gold };
  }
  function complement(c, needs, role) {
    if (!needs || !c.s) return null;
    const w = D.weights[role];
    let num = 0, den = 0;
    FAC.forEach((f, i) => { if (c.f[i] == null) return; const k = needs.gap[i] + 0.5 * (w[f] > 0 ? 1 : 0); num += k * (c.f[i] - c.note); den += k; });
    const gain = den ? num / den : 0;                       // forces relatives du candidat là où l'équipe est en retrait
    const res = Math.exp(-Math.pow(c.s[0] + needs.gold, 2) / (2 * 1.6 * 1.6)); // équilibre des ressources (or)
    return 100 * (0.5 * res + 0.5 / (1 + Math.exp(-gain / 1.8)));
  }
  function renderScout() {
    const sc = state.sc; const t = sc.tid ? team(sc.tid) : null;
    const lineup = $('#lineup'), brief = $('#brief'), rows = $('#scout-rows');
    $('#s-roles').querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.role === sc.role));
    let inc = null, needs = null;
    if (t) {
      $('#team-input').value = t.name;
      lineup.innerHTML = ROLES.map((r) => {
        const p = byId.get(t.roster[r]);
        return `<button data-role="${r}" aria-pressed="${r === sc.role}"><span class="role">${r}</span><span class="name">${p ? h(p.name) : 'Poste vacant'}</span><span class="num ${p ? noteCls(p.note) : 't-low'}">${p ? nInt(p.note) : '–'}</span><small>${p ? archetype(p) || '' : 'aucun titulaire récent'}</small></button>`;
      }).join('');
      lineup.hidden = false;
      inc = byId.get(t.roster[sc.role]) || null; needs = teamNeeds(t, sc.role);
    } else { lineup.hidden = true; lineup.innerHTML = ''; }
    if (sc.ref) inc = byId.get(sc.ref) || inc;
    // texte de cadrage
    let txt = '';
    if (t && needs) {
      const weakest = needs.gap.map((g, i) => [g, i]).filter((x) => x[0] >= 1.5).sort((a, b) => b[0] - a[0]).slice(0, 2).map((x) => FLABEL[FAC[x[1]]].toLowerCase());
      const res = needs.gold >= 1 ? 'Les quatre autres joueurs consomment beaucoup d\'or : un profil peu gourmand s\'intègre mieux.' : needs.gold <= -1 ? 'Les quatre autres joueurs consomment peu d\'or : il y a de la place pour un carry.' : 'Les ressources sont réparties de façon classique entre les quatre autres joueurs.';
      txt = `<b>${h(t.name)}</b> (${h(lgName(t.league))}, niveau ${nInt(t.lvl)}) cherche un <b>${sc.role}</b>${inc ? `, à la place de ${h(inc.name)} (${nInt(inc.note)}, ${(archetype(inc) || '').toLowerCase()})` : ''}. ` +
        (weakest.length ? `Le reste de l'équipe est en retrait sur : <b>${weakest.join('</b> et <b>')}</b>. ` : 'Le reste de l\'équipe n\'a pas de facette nettement en retrait. ') + res;
    } else if (inc) txt = `Joueurs au poste de <b>${sc.role}</b> comparés à <b>${h(inc.name)}</b> (${nInt(inc.note)}, ${(archetype(inc) || '').toLowerCase()}).`;
    else txt = `Choisissez une équipe pour chercher un renfort adapté à son effectif, ou parcourez directement les meilleurs <b>${ROLE_PL[sc.role]}</b>.`;
    brief.innerHTML = txt;
    // candidats
    let C = S.players.filter((p) => p.role === sc.role && p.n >= sc.minG && p.note >= sc.minNote && (!t || p.tid !== t.tid) && (!inc || p.id !== inc.id) && (!t || !sc.reach || p.team_lvl <= t.lvl + 1) &&
      (sc.tier === '' || p.tier === +sc.tier) && (!sc.region || p.region === sc.region) && (!sc.league || p.league === sc.league));
    C = C.map((p) => {
      const sim = inc ? similarity(p, inc) : null, comp = complement(p, needs, sc.role);
      const score = p.note + (comp != null ? (comp - 50) / 10 : 0) + (sim != null ? (sim - 40) / 25 : 0);
      return { p, sim, comp, score, delta: inc ? p.note - inc.note : null };
    });
    const key = { score: (x) => x.score, note: (x) => x.p.note, sim: (x) => x.sim || 0, comp: (x) => x.comp || 0 }[sc.sort];
    C.sort((a, b) => key(b) - key(a));
    $('#s-sort').value = sc.sort; $('#s-reach').checked = sc.reach; $('#s-reach').disabled = !t;
    $('#scout-count').textContent = `${fmt(C.length)} candidat${C.length > 1 ? 's' : ''}`;
    if (!C.length) { rows.innerHTML = '<p class="none">Aucun candidat avec ces critères. Baissez la note minimale ou élargissez les ligues.</p>'; return; }
    rows.innerHTML = C.slice(0, sc.shown).map((x, i) => {
      const p = x.p, ins = insights(p).plus.slice(0, 2).map((s) => s.replace(/<b>(.*?)<\/b>.*/, '$1'));
      const dl = x.delta == null ? '' : `<span class="trend ${x.delta >= 1 ? 'up' : x.delta <= -1 ? 'down' : 'flat'}">${x.delta > 0 ? '+' : ''}${fmt(x.delta, 1)}</span>`;
      const meter = (v) => v == null ? '<span class="meter"><span></span><b>–</b></span>' : `<span class="meter"><span class="bar"><i style="width:${v}%"></i></span><b>${fmt(v)}</b></span>`;
      return `<button class="row" data-p="${p.id}" data-cmp="${inc ? inc.id : ''}"><span class="rank">${i + 1}</span><span class="num note ${noteCls(p.note)}">${nInt(p.note)}</span>
        <span class="who"><b>${h(p.name)}</b><small>${h(p.team)}, ${h(lgName(p.league))}</small></span><span class="pos r">${dl}</span>
        <span class="m-sim">${meter(x.sim)}</span><span>${meter(x.comp)}</span><span class="pos games"><small>${archetype(p) || ''}${ins.length ? '<br>' + ins.join(', ') : ''}</small></span></button>`;
    }).join('') + (C.length > sc.shown ? '<button class="more" id="scout-more">Afficher 60 candidats de plus</button>' : '');
  }
  function suggest(q) {
    const box = $('#suggest'); q = q.trim().toLowerCase();
    if (!q) { box.hidden = true; return; }
    const T = S.teams.filter((t) => t.name.toLowerCase().includes(q)).sort((a, b) => b.lvl - a.lvl).slice(0, 12);
    box.innerHTML = T.length ? T.map((t) => `<button data-tid="${h(t.tid)}"><span>${h(t.name)}</span><small>${h(lgName(t.league))}</small></button>`).join('') : '<p class="none" style="padding:10px">Aucune équipe à ce nom cette saison.</p>';
    box.hidden = false;
  }

  /* ------------------------------------------------------------ méthode */
  function renderMethod() {
    const w = D.weights;
    $('#wtable').innerHTML = '<tr><th>Facette</th>' + ROLES.map((r) => `<th>${r}</th>`).join('') + '</tr>' +
      FAC.map((f) => `<tr><td>${FLABEL[f]}</td>${ROLES.map((r) => `<td>${w[r][f] ? fmt(w[r][f] * 100) + ' %' : '–'}</td>`).join('')}</tr>`).join('');
    const L = Object.entries(S.leagues).filter(([l]) => S.players.some((p) => p.league === l)).sort((a, b) => b[1] - a[1]);
    $('#lgs').innerHTML = L.map(([l, v]) => `<div class="lg"><span>${h(l)}</span><span class="bar"><i style="width:${Math.max(2, (v - 30) / 69 * 100)}%;background:${noteVar(v)}"></i></span><b>${nInt(v)}</b></div>`).join('');
    $('#m-season').textContent = state.season;
  }

  /* ------------------------------------------------------------ événements d'interface */
  function render() {
    document.querySelectorAll('.tabs button').forEach((b) => b.setAttribute('aria-selected', b.dataset.view === state.view));
    document.querySelectorAll('.view').forEach((v) => (v.hidden = v.id !== 'view-' + state.view));
    document.querySelectorAll('#season button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.season === state.season));
    if (state.view === 'rank') renderRank(); else if (state.view === 'scout') renderScout(); else renderMethod();
  }
  function init() {
    $('#season').innerHTML = Object.keys(D.seasons).sort().map((y) => `<button data-season="${y}">${y}</button>`).join('');
    load(); fillSelects();
    document.addEventListener('click', (e) => {
      const b = e.target.closest('button'); if (!b) { if (e.target.classList.contains('scrim')) closeSheet(); return; }
      if (b.dataset.view) { state.view = b.dataset.view; render(); window.scrollTo(0, 0); }
      else if (b.dataset.season) { state.season = b.dataset.season; state.sc.tid = null; state.sc.ref = null; $('#team-input').value = ''; load(); fillSelects(); render(); }
      else if (b.dataset.scout) { const p = byId.get(b.dataset.scout); closeSheet(); state.view = 'scout'; state.sc.role = p.role; state.sc.ref = p.id; const t = S.teams.find((x) => x.roster[p.role] === p.id); state.sc.tid = t ? t.tid : null; if (!t) $('#team-input').value = ''; render(); window.scrollTo(0, 0); }
      else if (b.dataset.p) openSheet(b.dataset.p, b.dataset.cmp);
      else if (b.hasAttribute('data-close')) closeSheet();
      else if (b.dataset.tid) { $('#suggest').hidden = true; setTeam(b.dataset.tid); }
      else if (b.id === 'more') { state.shown += 100; renderRank(); }
      else if (b.id === 'scout-more') { state.sc.shown += 60; renderScout(); }
      else if (b.id === 'reset') { Object.assign(state, { role: '', tier: '0', region: '', league: '', event: '', minG: 15, q: '', shown: 100 }); syncFilters(); fillSelects(); renderRank(); }
      else if (b.id === 'clear-team') { state.sc.tid = null; state.sc.ref = null; $('#team-input').value = ''; renderScout(); }
      else if (b.closest('#f-roles')) { state.role = b.dataset.role; state.shown = 100; syncFilters(); renderRank(); }
      else if (b.closest('#s-roles') || b.closest('#lineup')) { state.sc.role = b.dataset.role; state.sc.ref = null; state.sc.shown = 60; renderScout(); }
    });
    const bind = (id, fn) => $(id).addEventListener('input', (e) => { fn(e.target.value); state.shown = 100; state.sc.shown = 60; state.view === 'rank' ? renderRank() : renderScout(); });
    bind('#f-tier', (v) => { state.tier = v; }); bind('#f-region', (v) => { state.region = v; if (v) { state.league = ''; $('#f-league').value = ''; } });
    bind('#f-league', (v) => { state.league = v; if (v) { state.tier = ''; state.region = ''; syncFilters(); } });
    bind('#f-event', (v) => { state.event = v; if (v) { state.tier = ''; state.minG = 0; syncFilters(); } else { state.minG = 15; state.tier = '0'; syncFilters(); } });
    bind('#f-min', (v) => { state.minG = +v || 0; }); bind('#f-q', (v) => { state.q = v; });
    bind('#s-tier', (v) => { state.sc.tier = v; }); bind('#s-region', (v) => { state.sc.region = v; }); bind('#s-league', (v) => { state.sc.league = v; });
    bind('#s-sort', (v) => { state.sc.sort = v; }); $('#s-reach').addEventListener('change', (e) => { state.sc.reach = e.target.checked; state.sc.shown = 60; renderScout(); });
    bind('#s-note', (v) => { state.sc.minNote = +v || 0; }); bind('#s-min', (v) => { state.sc.minG = +v || 0; });
    $('#team-input').addEventListener('input', (e) => suggest(e.target.value));
    $('#team-input').addEventListener('focus', (e) => { e.target.select(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { closeSheet(); $('#suggest').hidden = true; } });
    syncFilters(); render();
  }
  function syncFilters() {
    $('#f-tier').value = state.tier; $('#f-region').value = state.region; $('#f-league').value = state.league; $('#f-min').value = state.minG; $('#f-q').value = state.q; $('#f-event').value = state.event;
    $('#f-roles').querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', b.dataset.role === state.role));
  }
  init();
})();
