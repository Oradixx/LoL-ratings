"""Construit page/lol-ratings-3.html à partir de results/page_data.json.
Tous les chiffres cités dans le texte viennent du JSON : relancer run_all.sh puis ce script met la page à jour."""
import json, html
D=json.load(open('results/page_data.json'))
CSS=open('page/style.css').read()

def n(x,d=0):
    s=f'{x:,.{d}f}'.replace(',',' ').replace('.',',')
    return s.replace(' ','&nbsp;')
def pct(x,d=0): return n(100*x,d)+'&nbsp;%'
def sgn(x,d=0): return ('+' if x>0 else '')+n(x,d)
E=html.escape

F=D['final']; R=D['rolling']['total']; M=D['rolling']['monthly']
V10F=F['v1.0 LoL Ratings 3.0']; ELOF=F['Elo équipe']; KDAF=F['v0.1 KDA']
V11=R['v1.2 rattachement mixte']; V11a=R['v1.1 ré-entraînée chaque mois']; ELO=R['Elo équipe (mis à jour à chaque game)']; ELOJ=R['Elo joueurs (mis à jour à chaque game)']
KDAR=R['KDA à date']; FROZ=R['v1.0 (2025 seul, gelée)']; COMB=R['v1.2 + Elo (combinés)']; TAU=R['v1.1 + oubli progressif (1 an)']
months_better=sum(1 for m in M['v1.2 rattachement mixte'] if M['v1.2 rattachement mixte'][m]['auc']>M['Elo équipe (mis à jour à chaque game)'][m]['auc'])
nmonths=len(M['v1.2 rattachement mixte'])
S=D['scouting']; U=D['underrated']; RT=D['ratones']; REL=D['reliab']; MV=D['mv']; TOP=D['top']
t50=D['v03_top50']; t50s=sorted(t50.items(),key=lambda kv:-kv[1])
top50_txt=', '.join(f'{v} de {k}' for k,v in t50s[:3])
pairs=D['pairs']
C=D['counter']; cp={k:C[k]['champ']/2 for k in C}; cpse={k:C[k]['champ_se']/2 for k in C}
TL={t['kind']:t for t in D['tilt']}
t_same=TL['même série (quelques minutes après)']; t_next=TL['prochaine rencontre (<60 j)']
maj=TOP['Ligue majeure']
no1={ro:maj[ro][0] for ro in maj}
no1_teams=[no1[r]['team'] for r in ['Top','Jungle','Mid','ADC','Support']]
ROLES=['Top','Jungle','Mid','ADC','Support']
import pandas as _pd
mvw={r:MV['roles']['Ligue majeure'][r][0] for r in ROLES}
GENG_GAMES=D.get('geng_games',0)
u0=U[0]
games25=D['games']['2025']; games26=D['games']['2026']
ch=MV['choice_effects']
MOIS=['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre']
def frdate(s):
    y,mo,d=s.split('-'); return f"{int(d)} {MOIS[int(mo)-1]} {y}"
_ws=D['worlds'].get('score')
WSCORE=(f'''<p class="verdict">Verdict, sur les {n(_ws['n_games'])} games de Worlds 2026 : le modèle gelé a bien prédit {pct(_ws['p_model']['acc'])} des games (AUC {n(_ws['p_model']['auc'],3)}, log-loss {n(_ws['p_model']['logloss'],3)}), contre {pct(_ws['p_elo']['acc'])} pour l'Elo d'équipe gelé le même jour (AUC {n(_ws['p_elo']['auc'],3)}). Séries : {pct(_ws['series_acc_p_model'])} contre {pct(_ws['series_acc_p_elo'])}.</p>''' if _ws and _ws.get('n_games') else '<p class="muted">Verdict : après la finale.</p>')
SIM=D['sim']; TRF=D['transfer']; CHC=D['champ']; CAL=D['calib']; WD=D['worlds']
_s1=SIM['sigma_100']; _s2=SIM['sigma_200']; _cov=lambda s:(s['cov1_stable']+s['cov1_mobile'])/2
_tg=TRF['_prior_gain']; _c2=CHC['<= 2 games']; _nb=CHC['new0_by_game_number']
SO=D['season_only']; SVAL=D['split_validation']; LPC=D['league_prior_check']; SE=D['split_examples']; SMV=D.get('season_mv_n',300)
_v12=SO['v1.2 rattachement mixte']; _v13=SO['v1.3 saison seule']
early=lambda d:sum(d['monthly'][m] for m in ['2026-02','2026-03'])/2; late=lambda d:sum(d['monthly'][m] for m in ['2026-08','2026-09'])/2
_cal=SE.get('Caliste'); _exo=SE.get('Exofeng')
def _pick(ex,key):
    return next((c for c in ex['comps'] if key(c['comp'])),None) if ex else None
cal_rs=_pick(_cal,lambda c:c.startswith('LEC Summer · saison')); cal_po=_pick(_cal,lambda c:c.startswith('LEC Summer · playoffs'))
exo_rs=_pick(_exo,lambda c:c.startswith('LFL') and 'saison' in c); exo_prm=[c for c in (_exo['comps'] if _exo else []) if c['comp'].startswith('PRM')]
exo_prm_g=sum(c['gp'] for c in exo_prm); exo_prm_w=sum(c['gp']*c['win'] for c in exo_prm)/max(1,exo_prm_g)
_RF={'Top':'en top','Jungle':'en jungle','Mid':'en mid','ADC':'en ADC','Support':'en support'}
_solid=[r for r in ROLES if mvw[r]['mv_p1']>=0.8]; _open=[r for r in ROLES if r not in _solid]
def _duo(r):
    L=MV['roles']['Ligue majeure'][r][:2]
    return _RF[r]+' entre '+E(L[0]['player'])+' ('+pct(L[0]['mv_p1'])+') et '+E(L[1]['player'])+' ('+pct(L[1]['mv_p1'])+')'
_geng=any(x['team']=='Gen.G' for r in _open for x in MV['roles']['Ligue majeure'][r][:2])
def _join(xs): return xs[0] if len(xs)==1 else ', '.join(xs[:-1])+' et '+xs[-1]
MV_TXT=((_join([E(mvw[r]['player']) for r in _solid])+(' est' if len(_solid)==1 else ' sont')+' n°1 dans '+('toutes les versions' if all(mvw[r]['mv_p1']>=0.995 for r in _solid) else 'presque toutes les versions')+'. ') if _solid else '')+\
       (('Le multivers hésite '+_join([_duo(r) for r in _open])+'. ') if _open else '')+\
       ((f"Ce n'est pas un hasard si Gen.G revient dans ces duels : l'équipe a aligné exactement les mêmes cinq joueurs toute la saison ({n(GENG_GAMES)} games ensemble). Aucune version ne peut dire lequel des cinq porte les autres, et c'est pour ça que les choix de modélisation font basculer le n°1.") if _geng else '')
_teams1=set(no1[r]['team'] for r in ROLES)
if len(_teams1)==1 and not _open:
    _t=list(_teams1)[0]
    MV_TXT+=f" Les cinq n°1 jouent tous chez {E(_t)}, et ce n'est pas un hasard. {E(_t)} a aligné exactement les mêmes cinq joueurs dans {n(GENG_GAMES)} de ses {n(D['geng_total'])} games : le modèle voit que c'est la meilleure équipe de 2026 (de peu devant {E(D['team_top2'][1]['team'])}), mais rien ne lui permet de dire lequel des cinq la porte. Il partage donc le mérite, et chacun se retrouve en tête de son poste. Changer les réglages n'y change rien, d'où le multivers unanime."
LC=D['league_check']; EM=D['em_check']; EXO=D['exofeng']; mov={x['origine']:x for x in LC['movers']}; LN=D['leagues_now']

BODY=f'''
<div class="wrap">
<header class="hero col">
  <span class="eyebrow">Projet data · LoL pro 2025-2026 · version par version</span>
  <h1>Qui est le meilleur joueur <em>de LoL</em> du monde&nbsp;?</h1>
  <p class="dek">Tout le monde a un avis. J'ai pris les {n(games25)} games pro de 2025, dans {D['leagues_2025_n']} ligues et tournois, et j'ai essayé de trancher avec un modèle. Chaque fois qu'il donnait une réponse, je cherchais pourquoi elle était fausse, puis je publiais un patch. À la fin, un juge que je ne pouvais pas influencer a noté le travail : les {n(games26)} games de 2026.</p>
  <div class="strip">
    <div><b class="num">{n(games25)}</b><span>games 2025 pour construire</span></div>
    <div><b class="num">{n(games26)}</b><span>games 2026 pour juger</span></div>
    <div><b class="num">{n(MV['auc']['n'])}</b><span>versions du modèle</span></div>
    <div><b class="num">{pct(V11['acc'],1)}</b><span>des games 2026 prédites en conditions réelles</span></div>
  </div>
  <p class="muted" style="font-size:14px">Inspiré de la méthode de la vidéo <a href="https://www.youtube.com/watch?v=0I2T0R91G38">« the most average NBA player »</a> (<a href="https://github.com/HQEye/basic-most-average-nba-player">code</a>) et parti du notebook <i>LoL Ratings 2.0</i>. Données : Oracle's Elixir, jusqu'au {frdate(D['data_until'])}.</p>
</header>

<section><div class="col">
  <span class="eyebrow">Avant de coder · la boucle d'idées</span>
  <h2>D'abord, choisir la bonne question</h2>
  <p>Je voulais un sujet qu'on ne trouve pas déjà tout fait sur internet. J'ai listé des idées, puis j'ai lancé une sonde rapide sur les plus prometteuses avant de m'engager.</p>
  <ul class="ideas" id="ideas"></ul>
  <p>La note joueur l'emporte parce qu'elle permet un test honnête. Entre deux saisons, les équipes changent de joueurs. Un bon modèle « joueur » doit donc prédire la saison suivante mieux qu'un modèle « équipe ». C'est une question vérifiable.</p>
</div></section>

<section><div class="col">
  <span class="eyebrow">Patch 0.1 · le labo, saison 2025</span>
  <div class="patch">
    <div class="patch-head"><span class="ver">0.1</span><span class="name">Le KDA</span></div>
    <div class="patch-body">
      <p>La stat que tout le monde regarde : (kills + assists) / morts. Minimum 15 games en 2025.</p>
      <div class="tbl-wrap"><table id="t-v01"></table></div>
      <p class="verdict">Le meilleur joueur du monde serait donc {E(D['v01'][0]['name'])}… en {E(D['v01'][0]['league'])}, la ligue régionale britannique et nordique, avec {pct(D['v01'][0]['W'])} de victoires.</p>
      <ul class="changes">
        <li><span class="tag bug">Problème</span><span>Le KDA mesure surtout si ton équipe gagne : corrélation de <b>{n(D['v01_corr'],2)}</b> avec le winrate du joueur. Une équipe qui écrase sa ligue donne des KDA énormes à ses cinq joueurs.</span></li>
        <li><span class="tag bug">Problème</span><span>Il ne sait pas contre qui tu joues. Dominer la NLC et dominer la LCK, ce n'est pas le même exploit.</span></li>
      </ul>
    </div>
  </div>
</div></section>

<section><div class="col">
  <span class="eyebrow">Patch 0.2</span>
  <div class="patch">
    <div class="patch-head"><span class="ver">0.2</span><span class="name">LoL Ratings 2.0, appliqué au monde entier</span></div>
    <div class="patch-body">
      <p>Ton notebook : des stats par rôle, pondérées à la main, normalisées en z-score, puis additionnées. Je l'ai appliqué tel quel à toutes les ligues au lieu de la seule LEC.</p>
      <div class="tbl-wrap"><table id="t-v02"></table></div>
      <ul class="changes">
        <li><span class="tag bug">Bug</span><span>Les z-scores sont calculés sur <i>tous les rôles mélangés</i>. Résultat : les poids choisis ne sont pas ceux qui s'appliquent. Une stat qui varie beaucoup entre rôles (les DPM) est écrasée ; une stat qui varie peu (le GD@10) prend le dessus.</span></li>
        <li><span class="tag bug">Bug</span><span>Une seule stat manquante annule toute la note : {n(D['v02_nan'])} joueurs n'ont pas de note, dont {n(D['v02_nan_jng'])} junglers (la stat « STL » n'existe pas dans les données game par game, et la LPL 2025 n'a pas de stats à 10 min).</span></li>
      </ul>
      <div class="tbl-wrap"><table id="t-eff"></table></div>
      <p class="muted" style="font-size:13.5px">Poids voulus ⇒ poids réellement appliqués (part de la variance intra-rôle), sur les {n(D['n15'])} joueurs à 15 games ou plus.</p>
    </div>
  </div>
</div></section>

<section><div class="col">
  <span class="eyebrow">Patch 0.3</span>
  <div class="patch">
    <div class="patch-head"><span class="ver">0.3</span><span class="name">Z-score par rôle</span></div>
    <div class="patch-body">
      <p>Correction du bug : chaque joueur est comparé aux joueurs de son rôle. Les stats manquantes valent la moyenne.</p>
      <p class="verdict">Le top&nbsp;50 mondial compte {top50_txt}… et {D['v03_top50_major']} joueur(s) des six ligues majeures.</p>
      <ul class="changes">
        <li><span class="tag bug">Problème</span><span>La ligue. Les stats sont relatives aux adversaires ; être le meilleur d'une petite ligue gonfle tout.</span></li>
        <li><span class="tag bug">Problème</span><span>La fraude électorale, comme dans la vidéo : DPM et DMG% sont corrélés à <b>{n(pairs.get('DMG|DPM',0),2)}</b>, GD@10 et XPD@10 à <b>{n(pairs.get('GD10|XPD10',0),2)}</b>, CSD@10 et XPD@10 à <b>{n(pairs.get('CSD10|XPD10',0),2)}</b>. Certaines compétences votent deux fois.</span></li>
        <li><span class="tag bug">Problème</span><span>Le champion. Un Azir et un Rakan ne font pas les mêmes DPM, quel que soit le joueur.</span></li>
        <li><span class="tag bug">Problème</span><span>Les poids sont toujours choisis à la main. Pourquoi 0,25 et pas 0,15&nbsp;?</span></li>
      </ul>
    </div>
  </div>
  <p>À ce stade, j'ai changé d'approche. Toutes les versions précédentes regardent les stats d'un joueur pour deviner son impact, alors que ces stats sont contaminées par l'équipe, le champion et la ligue. Il faut mesurer l'impact directement.</p>
</div></section>

<section><div class="col">
  <span class="eyebrow">Patch 0.4</span>
  <div class="patch">
    <div class="patch-head"><span class="ver">0.4</span><span class="name">Qui est sur la carte quand l'équipe gagne&nbsp;?</span></div>
    <div class="patch-body">
      <p>L'idée vient du basket (le « RAPM ») : on oublie les stats individuelles. Chaque game devient une équation.</p>
      <p class="mono" style="background:var(--bg);padding:12px 14px;font-size:14px;overflow-x:auto">écart d'or final = côté bleu + (5 notes bleues) − (5 notes rouges) + bruit</p>
      <p>Avec des milliers d'équations et quelques milliers d'inconnues, on résout pour trouver la note de chaque joueur. Un joueur est bien noté si son équipe fait mieux quand il est là, peu importe ses stats.</p>
      <ul class="changes">
        <li><span class="tag new">Nouveau</span><span>Régression ridge : les notes sont tirées vers zéro tant que les données ne prouvent rien. Un remplaçant avec 3 games ne peut pas finir n°1.</span></li>
        <li><span class="tag bug">Problème</span><span>Une équipe garde souvent le même cinq : en médiane, 2 compositions différentes par équipe sur l'année. Si cinq joueurs jouent toujours ensemble, aucune équation ne peut dire lequel porte les autres.</span></li>
      </ul>
    </div>
  </div>
</div></section>

<section><div class="col">
  <span class="eyebrow">Patch 0.5</span>
  <div class="patch">
    <div class="patch-head"><span class="ver">0.5</span><span class="name">Les ligues n'ont pas le même niveau</span></div>
    <div class="patch-body">
      <p>Chaque note devient « niveau de la ligue d'origine + écart individuel ». Les ligues sont reliées par les tournois internationaux (First Stand, MSI, EWC, Worlds, EMEA Masters, Asia Masters…) et par les joueurs qui changent de ligue.</p>
      <ul class="changes">
        <li><span class="tag bug">Raté</span><span>Premier essai : la LFL sortait ligue la plus forte du monde, la LCK 7<sup>e</sup>. J'avais attaché le niveau de ligue à l'<i>équipe</i> de chaque game, avec une pénalité trop faible. Les ERL ne jouent jamais contre la LEC : chaque « îlot » de ligues se recentrait sur zéro, et la LFL, reine de l'îlot ERL, montait au sommet.</span></li>
        <li><span class="tag buff">Correctif</span><span>Le niveau de ligue est porté par le <i>joueur</i> (sa ligue principale). Quand un joueur de LFL vient jouer en LEC, son match relie les deux ligues.</span></li>
        <li><span class="tag new">Noms</span><span>Les ligues changent de nom selon les années. En 2025, la LTA Nord regroupe les équipes de la LCS et la LTA Sud celles du CBLOL plus deux équipes LATAM ; en 2026, LCS et CBLOL reviennent. Je les fusionne sous leurs noms 2026. La « LTA » tout court (matchs croisés Nord/Sud) compte comme un tournoi international, et la SuperLiga espagnole devient la LES.</span></li>
      </ul>
    </div>
  </div>
  <figure>
    <div class="ftitle">Le niveau des ligues selon le modèle (2025-2026)</div>
    <div id="f-leagues"></div>
    <figcaption>Points LR3 du joueur moyen de chaque ligue (0 = joueur moyen actif en 2026). 100 points ≈ 500 golds d'écart final par game et par joueur. Modèle entraîné sur toutes les games jusqu'au {frdate(D['data_until'])}. Les ligues peu reliées aux autres ont les estimations les plus fragiles.</figcaption>
  </figure>
  <div class="callout"><span class="eyebrow">LCK CL ou LEC&nbsp;?</span><p>Avec la seule saison 2025, le modèle mettait la LCK Challengers au niveau de la LEC ({sgn(LC['diff']['LCKC-LEC'][0])} points, avec une incertitude de ±{n(LC['diff']['LCKC-LEC'][1])}) : trop peu de joueurs relient les deux ligues pour trancher. Les transferts de l'intersaison ont servi de test. Les joueurs partis de la LCK CL vers une autre ligue ont fait {sgn(mov['LCKC']['points_par_joueur'])} points par joueur par rapport à leur note 2025 (±{n(mov['LCKC']['se'])}), ceux partis de la LEC {sgn(mov['LEC']['points_par_joueur'])} (±{n(mov['LEC']['se'])}). La LEC était donc sous-estimée. Une fois 2026 intégrée, la LEC passe nettement devant ({sgn(LN['LEC'])} contre {sgn(LN['LCKC'])}).</p></div>
  <div class="callout"><span class="eyebrow">Et les EMEA Masters&nbsp;?</span><p>Elles comptent, comme tous les tournois : leurs {n(EM['em_games'])} games (2025-2026) sont le seul endroit où les ERL s'affrontent directement. Pour les grosses ERL, reliées à la LEC par de nombreux transferts, elles changent peu de chose (LFL {sgn(EM['with']['LFL']['vs_lec'])} points sous la LEC avec, {sgn(EM['without']['LFL']['vs_lec'])} sans). Pour les petites, elles font la différence : sans les EM, la Tchéquie-Slovaquie (HM) passerait de {sgn(EM['with']['HM']['vs_lec'])} à {sgn(EM['without']['HM']['vs_lec'])} et l'Italie (LIT) de {sgn(EM['with']['LIT']['vs_lec'])} à {sgn(EM['without']['LIT']['vs_lec'])}, avec une incertitude plus large d'environ 15&nbsp;%.</p></div>
</div></section>

<section><div class="col">
  <span class="eyebrow">Patch 0.6 à 0.8</span>
  <div class="patch">
    <div class="patch-head"><span class="ver">0.6</span><span class="name">La machine choisit les poids</span></div>
    <div class="patch-body">
      <p>Le RAPM seul est très bruité. Je lui donne un point de départ : une note « stats » par rôle, sans poids à la main. La machine apprend quelles stats ressemblent à l'impact mesuré en 0.4. Surtout pas celles qui prédisent la victoire : ce serait réintroduire l'équipe par la porte de derrière.</p>
      <ul class="changes">
        <li><span class="tag new">Nouveau</span><span>Stats corrigées du champion (moyenne du champion à ce rôle) et exprimées par rapport à la ligue du joueur.</span></li>
        <li><span class="tag new">Nouveau</span><span>Un jeu de poids différent par rôle.</span></li>
      </ul>
    </div>
  </div>
  <figure class="bleed">
    <div class="ftitle">Ce que la machine retient, rôle par rôle</div>
    <div class="tbl-wrap" id="f-heat"></div>
    <figcaption>Golds d'écart final par game associés à +1 écart-type (à l'échelle d'une game) sur la stat, toutes les autres stats égales. Bleu = la stat signale un joueur à impact ; orange = l'inverse. La part de l'or de l'équipe est négative parce que, à or/minute égal, prendre une plus grosse part du gâteau de l'équipe n'aide pas.</figcaption>
  </figure>
  <div class="patch">
    <div class="patch-head"><span class="ver">0.7</span><span class="name">L'or plutôt que la victoire</span></div>
    <div class="patch-body">
      <ul class="changes">
        <li><span class="tag buff">Buff</span><span>La cible devient l'écart d'or final, pas seulement victoire/défaite. Une victoire à +15&nbsp;k et une victoire arrachée à +500 ne racontent pas la même chose. Sur {n(MV['auc']['n'])} versions du modèle, la cible « or » fait en moyenne {n(ch['target']['gold'],3)} d'AUC contre {n(ch['target']['result'],3)} pour la victoire seule.</span></li>
      </ul>
    </div>
  </div>
  <div class="patch">
    <div class="patch-head"><span class="ver">0.8</span><span class="name">Ce qui n'a rien changé</span></div>
    <div class="patch-body">
      <ul class="changes">
        <li><span class="tag nerf">Sans effet</span><span>La correction du champion : AUC moyenne {n(ch['champ']['False'],3)} sans, {n(ch['champ']['True'],3)} avec. Je la garde parce qu'elle est défendable, pas parce qu'elle aide.</span></li>
        <li><span class="tag nerf">Sans effet</span><span>Les stats de lane à 15 min : {n(ch['lane']['False'],3)} sans, {n(ch['lane']['True'],3)} avec.</span></li>
        <li><span class="tag nerf">Abandonné</span><span>L'oubli progressif (les games récentes comptent plus) : aucun gain, ni dans le multivers ni dans le test 2026.</span></li>
      </ul>
    </div>
  </div>
</div></section>

<section><div class="col">
  <span class="eyebrow">Patch 1.1 · ce que 2026 a appris au modèle</span>
  <div class="patch">
    <div class="patch-head"><span class="ver">1.1</span><span class="name">Relire son code avec plus de données</span></div>
    <div class="patch-body">
      <p>Avec le fichier 2025 complet (Worlds et intersaison compris) et la saison 2026, le modèle a de nouveau placé la LFL devant la LEC. Cette fois, ce n'était pas un réglage, c'était un bug.</p>
      <ul class="changes">
        <li><span class="tag bug">Bug</span><span>Les joueurs vus uniquement en tournoi (EMEA Masters, KeSPA Cup, Demacia Cup…) partageaient un seul groupe « international ». Ce fourre-tout reliait artificiellement des ligues qui ne se sont jamais affrontées.</span></li>
        <li><span class="tag buff">Correctif</span><span>Chaque tournoi garde son propre groupe, et les coupes sont détectées automatiquement (une ligue où la majorité des équipes jouent surtout ailleurs). Les ERL repassent derrière les ligues majeures.</span></li>
        <li><span class="tag new">Nouveau</span><span>Le modèle est ré-entraîné chaque mois sur tout ce qui s'est joué avant.</span></li>
      </ul>
    </div>
  </div>
  <div class="patch">
    <div class="patch-head"><span class="ver">1.2</span><span class="name">Le cas Exofeng</span></div>
    <div class="patch-body">
      <p>Question d'un lecteur : pourquoi Exofeng, rookie ADC très attendu, est-il si bas&nbsp;? En LFL 2026, Skillcamp gagne {pct(EXO['wr_with'])} de ses games avec lui et {pct(EXO['wr_without'])} avec l'autre ADC de l'équipe, et il a le meilleur KDA des ADC de la ligue.</p>
      <ul class="changes">
        <li><span class="tag bug">Bug</span><span>Chaque joueur était rattaché à la ligue où il avait joué le plus de games sur deux ans. Pour Exofeng, c'était la NLC (2025), pas la LFL où il joue aujourd'hui. Sa note partait donc du niveau de la NLC, et la régularisation l'empêchait de remonter assez. Tous les joueurs qui montent d'une ligue plus faible étaient sous-estimés de la même façon.</span></li>
        <li><span class="tag buff">Correctif</span><span>Le rattachement devient un mélange des ligues jouées, pondéré par la récence (demi-vie de 6 mois). Exofeng passe de {n(EXO['before'])} à {n(EXO['after'])} points, {EXO['rank_after']}<sup>e</sup> ADC de LFL. Sur la saison 2026, la prédiction reste au même niveau (AUC {n(V11['auc'],3)} contre {n(V11a['auc'],3)}) : le correctif ne se paie pas en précision, il corrige des cas comme le sien.</span></li>
        <li><span class="tag new">Limite</span><span>Pourquoi pas plus haut&nbsp;? Ses {EXO['n_recent']} games avec Skillcamp (LFL et EMEA Masters) sont gagnées à {pct(EXO['wr_recent'])}, mais les {EXO['n_before']} d'avant (NLC, LES, Prime League) à {pct(EXO['wr_before'])}, et le modèle pèse toutes les games de la même façon. Donner plus de poids aux games récentes ne prédit pas mieux en moyenne, donc je ne l'ai pas fait. Avec ±{n(EXO['sd'])} points d'incertitude, il peut tout à fait être le meilleur ADC de LFL : les données ne suffisent pas encore à le dire. Sa fiche, dans l'explorateur, montre la montée mois par mois.</span></li>
      </ul>
    </div>
  </div>
  <div class="patch">
    <div class="patch-head"><span class="ver">1.3</span><span class="name">Une note par saison, et par compétition</span></div>
    <div class="patch-body">
      <p>Deuxième remarque de lecteur : noter un joueur sur deux saisons mélange des contextes qui n'ont rien à voir. Il change de ligue ou d'équipe, ou tombe pendant un split sur une méta qui ne lui convient pas.</p>
      <ul class="changes">
        <li><span class="tag buff">Changement</span><span>Les notes affichées ne viennent plus que d'une saison. Pour 2026, le modèle part du niveau des ligues estimé sur 2025, puis n'apprend que sur les games de 2026. Cet a priori est volontairement ferme, parce qu'une ligue ne change pas de niveau du jour au lendemain : sur le rejeu de 2026 mois par mois, il fait passer l'AUC de {n(LPC['rolling']['None']['auc'],3)} à {n(LPC['rolling']['100']['auc'],3)}, et ne coûte rien ailleurs. L'onglet 2025 ne voit que la saison 2025.</span></li>
        <li><span class="tag new">Nouveau</span><span>Dans l'explorateur, un filtre par compétition et par split, saison régulière et playoffs séparés. La note sur une compétition = la note de saison + un écart mesuré sur l'écart d'or final des seules games de cette compétition.</span></li>
        <li><span class="tag bug">Contrôle</span><span>Ma première version faisait partir cet écart des stats du joueur sur la compétition. Test hors échantillon : les games de chaque compétition coupées en deux au hasard, l'écart appris sur une moitié, jugé sur l'autre. Les stats d'un split ne prédisent rien des autres games du même split (corrélation {n(SVAL['2025']['stats seules ×1']['corr'],2)} en 2025, {n(SVAL['2026']['stats seules ×1']['corr'],2)} en 2026), et l'écart dégradait la prédiction. Je les ai retirées. L'écart d'or final garde un peu de signal, à condition d'être très régularisé : réglage choisi sur 2025 avec un critère fixé d'avance, puis confirmé sur 2026.</span></li>
        <li><span class="tag new">Leçon</span><span>L'écart propre à un joueur sur un split est petit : de l'ordre de ±{n(D['split_prior_sd']['2026'])} points, alors que l'écart-type entre les joueurs d'un même poste en ligue majeure est de {n(D['role_sd'])} points. Une méta qui ne convient pas à un joueur existe sans doute, mais sur 10 à 30 games elle se noie dans le bruit. Et dans un roster qui ne change pas, les cinq joueurs reçoivent le même écart : rien ne permet de dire lequel a porté l'équipe ce split-là. Victoires et KDA de la compétition restent affichés à côté pour le contexte.</span></li>
        <li><span class="tag bug">Limite</span><span>Pour prédire, l'historique reste utile. J'ai rejoué la saison 2026 avec un modèle qui ne voit que les games de 2026 : AUC {n(_v13['auc'],3)} contre {n(_v12['auc'],3)}. Presque tout l'écart vient du début de saison (février-mars : {n(early(_v13),3)} contre {n(early(_v12),3)}) : un joueur qui n'a pas encore joué cette saison est inconnu du modèle, et en mars, quand les splits régionaux démarrent, c'est le cas de {pct(D['unseen_march'])} des joueurs alignés. En août-septembre, les deux font jeu égal ({n(late(_v13),3)} contre {n(late(_v12),3)}). Même pour décrire 2026 (des games de 2026 tirées au hasard et mises de côté), le modèle deux saisons fait un peu mieux : {n(D['halves_history']['deux saisons'],3)} contre {n(D['halves_history']['saison seule'],3)}. C'est le prix d'une note qui ne dépend que de la saison. Les notes affichées portent donc sur une saison, et les prédictions du juge, plus bas, utilisent tout l'historique.</span></li>
      </ul>
      <p>Deux exemples. Caliste (Karmine Corp) : note de saison {n(_cal['points'])}, {_cal['rank']}<sup>e</sup> ADC de LEC. Sur la saison régulière du Summer ({cal_rs['gp']} games, {pct(cal_rs['win'])} de victoires), sa note de compétition est de {n(cal_rs['note'])} ({sgn(cal_rs['d'],0)}){', le même écart que ses coéquipiers' if cal_rs['same_as_mates'] else ''} ; en playoffs du Summer, {n(cal_po['note'])} ({sgn(cal_po['d'],0)}).</p>
      <p>Exofeng, sur la seule saison 2026 : {n(_exo['points'])} points, {_exo['rank']}<sup>e</sup> ADC de LFL sur {_exo['n_role']}. Ses {D['exofeng_split']['n_early']} premières games de l'année, avant Skillcamp (Prime League, CCWS), ont été gagnées à {pct(D['exofeng_split']['wr_early'])}. Sans elles, le même modèle le met à {n(D['exofeng_split']['skillcamp_only'])}. C'est exactement le cas d'une saison qui mélange deux contextes. Le filtre de compétition ne le corrige presque pas (saison régulière de LFL : {n(exo_rs['note'])}, {sgn(exo_rs['d'],0)}), parce qu'en moyenne, chez tous les joueurs, l'écart d'une compétition à l'autre est surtout du bruit. Pour un cas comme le sien, le chiffre à retenir est l'incertitude : ±{n(_exo['sd'])} points.</p>
    </div>
  </div>
  <div class="patch">
    <div class="patch-head"><span class="ver">1.4</span><span class="name">Trois contrôles, aucun réglage changé</span></div>
    <div class="patch-body">
      <p>Plutôt que d'ajouter des boutons, j'ai vérifié le raisonnement lui-même, avec des tests que le modèle ne pouvait pas influencer.</p>
      <ul class="changes">
        <li><span class="tag bug">Contrôle</span><span><b>Une simulation où la vérité est connue.</b> Mêmes games, mêmes joueurs, mêmes coéquipiers, même bruit que la saison 2026, mais des notes « vraies » tirées au hasard, avec une part de talent que les stats ne voient pas (±100 à ±200 points). Le modèle retrouve les notes (corrélation {n(_s2['corr'],2)} à {n(_s1['corr'],2)}, erreur typique {n(_s1['rmse'])} à {n(_s2['rmse'])} points), et ses ± sont à peu près honnêtes : la vraie note tombe dans ±1 écart-type pour {pct(_cov(_s2))} à {pct(_cov(_s1))} des joueurs selon la part de talent invisible (68 % attendus). En revanche, dans un roster qui joue toujours ensemble, l'ordre entre coéquipiers n'est retrouvé qu'à {n(_s2['pair_corr_stable'],2)}-{n(_s1['pair_corr_stable'],2)} (corrélation), contre {n(_s2['pair_corr_other'],2)}-{n(_s1['pair_corr_other'],2)} ailleurs. Et le vrai n°1 d'un poste n'est désigné que dans {pct(_s2['no1_found'])} à {pct(_s1['no1_found'])} des cas. Le cas Gen.G, chiffré.</span></li>
        <li><span class="tag bug">Contrôle</span><span><b>Le partage du mérite, jugé sur les transferts.</b> Prédire les matchs ne dit pas comment répartir le mérite entre cinq joueurs inséparables ; un transfert, si. Notes 2025 gelées, jugées sur les {n(_tg['n'])} games 2026 où une équipe aligne au moins deux joueurs qui ont changé d'équipe. Le prior box-score aide vraiment (+{n(_tg['auc_gain'],4)} d'AUC, intervalle à 95 % [{n(_tg['lo'],4)} ; {n(_tg['hi'],4)}]). Et les réglages publiés sont déjà au sommet : plus ou moins de prior, de régularisation, avec ou sans stats de lane à 15 minutes, les variantes font jeu égal à 0,001 d'AUC près ou moins bien, sur janvier-mars comme sur avril-septembre. Rien qui justifie de changer.</span></li>
        <li><span class="tag bug">Contrôle</span><span><b>La méta, regroupée sur la saison.</b> Un joueur sur un champion qu'il a joué au plus deux fois en match officiel ({pct(_c2['share'])} des picks en 2026) ne fait pas moins bien que sa note. En moyenne, c'est même l'inverse (+{n(_c2['gold_per_player'])} ± {n(_c2['gold_se'])} golds par joueur concerné), sans doute parce qu'on sort un nouveau champion quand il est fort. L'ajouter au modèle n'améliore pas la prédiction hors échantillon. Le fearless draft, lui, se voit : la part de champions jamais joués passe de {pct(_nb['1'])} en game 1 d'une série à {pct(_nb['5'])} en game 5.</span></li>
      </ul>
      <p class="verdict">Quand un test ne montre rien, la bonne réponse est de ne rien toucher. Le vrai angle mort reste les rosters inséparables : seules plus de données (2023-2024, mercato 2027) le réduiront.</p>
    </div>
  </div>
</div></section>

<section><div class="col">
  <span class="eyebrow">Le juge · examen final</span>
  <h2>Est-ce que ça prédit 2026&nbsp;?</h2>
  <p>La vidéo n'avait aucun moyen de savoir si une définition était meilleure qu'une autre. Ici, si. Deux épreuves.</p>
  <h3>1. L'intersaison</h3>
  <p>Notes 2025 gelées, calibrées sur janvier 2026, jugées sur les {n(V10F['n'])} games de février 2026. Entre-temps, les effectifs ont été mélangés.</p>
  <figure>
    <div class="ftitle">Pouvoir prédictif sur février 2026</div>
    <div id="f-final"></div>
    <figcaption>AUC : probabilité que le modèle donne plus de chances au vainqueur qu'au perdant (0,5 = hasard). Entre parenthèses, le pourcentage de games bien prédites.</figcaption>
  </figure>
  <div class="grid2">
    <div class="callout"><span class="eyebrow">Le moment clé</span><p>L'Elo d'équipe s'effondre à l'intersaison ({pct(ELOF['acc'])} de bonnes prédictions) : le nom de l'équipe ne dit plus qui joue. Un modèle qui suit les joueurs garde son information ({pct(V10F['acc'],1)}).</p></div>
    <div class="callout"><span class="eyebrow">Los Ratones en LEC</span><p>Promus en LEC en 2026 avec Rekkles. Sur leurs {RT['n']} games : le KDA prévoyait <b>{pct(RT['kda'])}</b> de victoires, la v1.0 <b>{pct(RT['v1'])}</b>. Réalité : <b>{pct(RT['actual'])}</b>.</p></div>
  </div>
  <h3>2. Toute la saison 2026, en conditions réelles</h3>
  <p>Chaque mois, le modèle est ré-entraîné sur tout ce qui s'est joué avant le 1<sup>er</sup>, puis prédit les games du mois. Je lui oppose un Elo mis à jour après <i>chaque game</i>, ce qui l'avantage. {n(V11['n'])} games de février à septembre.</p>
  <figure>
    <div class="ftitle">Février → septembre 2026</div>
    <div id="f-rolling"></div>
    <figcaption>AUC sur {n(V11['n'])} games, avec son intervalle de confiance à 95&nbsp;% (bootstrap). Entre parenthèses, le pourcentage de games bien prédites.</figcaption>
  </figure>
  <figure>
    <div class="ftitle">Mois par mois</div>
    <div id="f-monthly"></div>
    <figcaption>AUC de chaque mois. La v1.0 gelée (notes 2025 jamais mises à jour) décroche en fin de saison ; la v1.2 ré-entraînée tient.</figcaption>
  </figure>
  <p>La v1.2 (ré-entraînée chaque mois) fait mieux que l'Elo d'équipe {months_better} mois sur {nmonths}. La combiner avec les deux Elo n'apporte rien (AUC {n(COMB['auc'],3)} contre {n(V11['auc'],3)}) : l'Elo ne sait rien que le modèle ne sache déjà. L'oubli progressif n'aide pas non plus ({n(TAU['auc'],3)}).</p>
  <p>Deux vérifications contre l'auto-persuasion. Un placebo : si je mélange au hasard les résultats de 2025, le modèle retombe à une AUC de {n(D['placebo'],2)} sur janvier 2026. Il ne triche donc pas. Et la stabilité : en coupant 2025 en deux moitiés au hasard, les notes des deux moitiés sont corrélées à {n(REL['v1 theta'],2)}. Le KDA fait {n(REL['KDA'],2)}, mais il est stable parce que la force d'une équipe est stable. Stable ne veut pas dire juste.</p>
  <h3>3. Les probabilités annoncées sont-elles justes&nbsp;?</h3>
  <p>Bien classer ne suffit pas : quand le modèle annonce 70&nbsp;%, l'équipe doit gagner 7 fois sur 10.</p>
  <figure>
    <div class="ftitle">Probabilité annoncée contre victoires réelles, 2026</div>
    <div id="f-calib"></div>
    <figcaption>Games de février à septembre 2026 regroupées par probabilité annoncée (v1.2 ré-entraînée chaque mois). Une courbe parfaite suit la diagonale.</figcaption>
  </figure>
  <p>L'écart moyen entre annoncé et réel est de {pct(CAL['games']['v1.2']['ece'],1)}. En log-loss (plus bas = mieux), la v1.2 fait {n(CAL['games']['v1.2']['logloss'],3)}, contre {n(CAL['games']['Elo équipe']['logloss'],3)} pour l'Elo d'équipe, {n(CAL['games']['Elo joueurs']['logloss'],3)} pour l'Elo des joueurs et {n(CAL['games']['taux bleu constant']['logloss'],3)} pour « toujours le taux de victoire du côté bleu ». Sur les séries, en partant de la probabilité d'avant la game 1 : {pct(CAL['series']['Bo3']['v1.2']['acc'])} des Bo3 bien prédits ({pct(CAL['series']['Bo3']['Elo équipe']['acc'])} pour l'Elo d'équipe) et {pct(CAL['series']['Bo5']['v1.2']['acc'])} des Bo5 ({pct(CAL['series']['Bo5']['Elo équipe']['acc'])}).</p>
</div></section>

<section><div class="col">
  <span class="eyebrow">Les notes 2026 · le multivers</span>
  <h2>Qui est le meilleur à chaque poste&nbsp;?</h2>
  <p>Comme dans la vidéo, je ne choisis pas une version. J'en tire {n(MV['auc']['n'])} au hasard, toutes défendables : force de la régularisation, cible (victoire, or, mélange), poids par rôle ou globaux, correction du champion, stats de lane, chaque stat retirée avec une probabilité de 15&nbsp;%, oubli progressif, minimum de games, rattachement du joueur à une ligue (la plus jouée ou un mélange). Chaque version est notée sur août-septembre 2026 (AUC de {n(MV['auc']['min'],3)} à {n(MV['auc']['max'],3)}). Pour les notes affichées, {n(SMV)} de ces versions sont ensuite ré-entraînées sur la seule saison choisie.</p>
  <p>Trois niveaux, jamais mélangés dans un même classement, parce que leurs joueurs ne s'affrontent presque jamais : les <b>ligues majeures</b> (LCK, LPL, LEC, LCS, CBLOL, LCP) ; le <b>2<sup>e</sup> niveau</b> (LCK Challengers, ERL comme la LFL ou la Prime League, NACL, Circuito Desafiante, ligues du Pacifique…) ; le <b>3<sup>e</sup> niveau</b> (LCK Academy Series, Nexus League, Hitpoint Challengers). Choisis un niveau, puis affine par région, ligue ou poste.</p>
  <div class="explorer bleed">
    <div class="xbar">
      <div class="role-tabs" role="group" aria-label="Saison" id="x-season">
        <button type="button" id="x-season-2026" data-v="2026" aria-pressed="true">Saison 2026</button>
        <button type="button" id="x-season-2025" data-v="2025" aria-pressed="false">Saison 2025</button>
      </div>
      <div class="role-tabs" role="group" aria-label="Vue" id="x-view">
        <button type="button" id="x-view-P" data-v="P" aria-pressed="true">Joueurs</button>
        <button type="button" id="x-view-T" data-v="T" aria-pressed="false">Équipes</button>
      </div>
      <div class="role-tabs" role="group" aria-label="Niveau" id="x-tier">
        <button type="button" id="x-tier-M" data-v="M" aria-pressed="true">Ligues majeures</button>
        <button type="button" id="x-tier-2" data-v="2" aria-pressed="false">2<sup>e</sup> niveau</button>
        <button type="button" id="x-tier-3" data-v="3" aria-pressed="false">3<sup>e</sup> niveau</button>
      </div>
    </div>
    <div class="controls">
      <label for="x-region">Région<select id="x-region"></select></label>
      <label for="x-league">Ligue<select id="x-league"></select></label>
      <label for="x-comp" class="p-only">Compétition / split<select id="x-comp"></select></label>
      <label for="x-role" class="p-only">Poste<select id="x-role"><option value="">Tous</option><option>Top</option><option>Jungle</option><option>Mid</option><option>ADC</option><option>Support</option></select></label>
      <label for="x-path" class="p-only">Parcours<select id="x-path"><option value="">Tous</option><option value="new">Nouveaux cette saison</option><option value="moved">Ont changé de ligue</option><option value="up">Promus en ligue majeure</option><option value="down">Redescendus</option></select></label>
      <label for="x-sort" class="p-only">Trier par<select id="x-sort"></select></label>
      <label for="x-unit">Unité<select id="x-unit"><option value="pts">Points LR3</option><option value="gold">Golds par game</option></select></label>
      <label for="x-min" class="p-only"><span id="x-min-l">Games min.</span> <span class="mono" id="x-min-v">20</span><input type="range" id="x-min" min="10" max="120" step="5" value="20"></label>
      <label for="x-q" class="grow">Chercher<input type="search" id="x-q" placeholder="joueur ou équipe" autocomplete="off"></label>
    </div>
    <p class="muted x-info" id="x-info"></p>
    <div id="x-cmp" class="x-cmp" hidden></div>
    <div class="tbl-wrap"><table id="x-table"></table></div>
    <button type="button" class="x-more" id="x-more">Afficher 25 de plus</button>
  </div>
  <p class="muted" style="font-size:13.5px" id="x-legend-P">Notes d'une seule saison : le modèle ne voit que les games de la saison choisie (pour 2026, le niveau des ligues part de 2025, puis les games de 2026 le corrigent). Choisis une compétition ou un split pour voir la note du joueur sur cette compétition : sa note de saison plus un écart mesuré sur l'écart d'or de ces games, très régularisé (patch 1.3 : l'écart propre à un split est petit, et le même pour les cinq joueurs d'un roster stable). Clique sur un joueur pour sa fiche : évolution mois par mois, parcours, toutes ses compétitions, et un bouton pour le comparer à d'autres joueurs (jusqu'à quatre, avec la probabilité que l'un soit vraiment meilleur que l'autre). « vs rôle » = golds d'écart final par game par rapport au joueur moyen du même poste dans sa ligue. « N°1 multivers » = part de 300 versions du modèle où il est n°1 de son poste, dans son niveau.</p>
  <p class="muted" style="font-size:13.5px" id="x-legend-T" hidden>Effectif = pour chaque poste, le joueur le plus présent sur les 20 dernières games de l'équipe dans la saison choisie. Force = note moyenne de ces cinq joueurs. « Contre l'équipe moyenne » = probabilité de battre une équipe moyenne de la même ligue, côté neutre. Le bilan réel de la saison est à côté pour comparer.</p>
  <p class="verdict">Version de référence : {', '.join(E(no1[r]['name'])+' ('+E(no1[r]['team'])+')' for r in ROLES)}. Le multivers, lui, désigne {', '.join(E(mvw[r]['player'])+' ('+pct(mvw[r]['mv_p1'])+')' for r in ROLES)}.</p>
  <p>{MV_TXT}</p>
  <p>L'incertitude statistique le confirme : un n°1 de la version de référence ne l'est que dans {pct(min(no1[r]['post_p1'] for r in no1))} à {pct(max(no1[r]['post_p1'] for r in no1))} des tirages. Un multivers protège contre les choix arbitraires, pas contre le manque de données.</p>
</div></section>

<section><div class="col">
  <span class="eyebrow">Ce que le modèle sait vraiment faire</span>
  <h2>Repérer les joueurs avant le mercato</h2>
  <p>J'ai pris les {n(S['n'])} joueurs hors ligues majeures en 2025 et regardé qui jouait en ligue majeure en 2026 (LCK, LPL, LEC, LCS, CBLOL, LCP).</p>
  <div class="grid2">
    <figure><div class="big num">{pct(S['top20_rate'])}</div><figcaption>des 20 joueurs les mieux notés par la v1.0 (notes 2025) jouent en ligue majeure en 2026. Taux de base : {pct(S['base'],1)} ({S['n_prom']} promus sur {n(S['n'])}).</figcaption></figure>
    <figure><div class="ftitle">Qui prédit les promotions&nbsp;?</div><div id="f-scout"></div><figcaption>AUC pour distinguer les promus des autres. Une partie de l'avance de la v1.0 vient du niveau estimé des ligues.</figcaption></figure>
  </div>
  <p>Et aujourd'hui, le joueur le plus sous-coté hors ligue majeure :</p>
  <div class="tbl-wrap bleed"><table id="t-under"></table></div>
  <p class="verdict">{E(u0['player'])}, {E(u0['role']).lower() if u0['role']!='ADC' else 'ADC'} de {E(u0['team'])} ({E(u0['league26'])}) : n°1 des joueurs hors ligue majeure dans {pct(u0['p1'])} des versions du modèle, top&nbsp;10 dans {pct(u0['p10'])}.</p>
  <p class="muted">Avec la réserve qui s'impose : {E(u0['player'])} a joué avec {u0['teammates']} coéquipiers différents cette saison. Plus ce nombre est petit, plus sa note peut appartenir en partie à son équipe. Même angle mort que Gen.G, en plus petit.</p>
</div></section>

<section><div class="col">
  <span class="eyebrow">Le prochain juge · figé le {frdate(WD['frozen_on'])}</span>
  <h2>Pronostics Worlds 2026</h2>
  <p>Worlds 2026 se joue de mi-octobre au 14 novembre, aux États-Unis. Le modèle de prédiction (v1.2, tout l'historique jusqu'au {frdate(WD['data_until'])}) est gelé dans <code>results/worlds2026/frozen_model.json</code>, et le commit qui l'ajoute en fait la date. Après la finale, un script le notera sur les games réelles, avec les compositions réellement alignées, contre un Elo d'équipe gelé le même jour. Rien ne sera ré-entraîné entre les deux.</p>
  {WSCORE}
  <div class="tbl-wrap bleed"><table id="t-worlds"></table></div>
  <div class="calc">
    <label for="w-a">Équipe A<select id="w-a"></select></label>
    <label for="w-b">Équipe B<select id="w-b"></select></label>
    <div id="w-out" class="w-out" aria-live="polite"></div>
  </div>
  <p class="muted" style="font-size:13.5px">Force = note moyenne des cinq titulaires (joueur le plus présent à chaque poste sur les 20 dernières games de ligue), en points. Probabilités côté neutre, games supposées indépendantes pour les Bo3 et Bo5. Toutes les équipes des ligues majeures sont proposées : la liste des qualifiés n'était pas complète le jour du gel.</p>
</div></section>

<section><div class="col">
  <span class="eyebrow">Bonus · les sondes</span>
  <h2>Deux idées testées, deux mythes dégonflés</h2>
  <figure>
    <div class="ftitle">Combien rapporte un counterpick&nbsp;?</div>
    <div id="f-counter"></div>
    <figcaption>Avance en or à 15 min du laner choisi après son adversaire direct, à côté, force des équipes (Elo) et force du champion égaux. ≈{n(C['top']['n']/2)} duels de lane par rôle (2022, 2025, 2026). Barres = ±2 erreurs-types. Pour comparer : un kill vaut 300 golds.</figcaption>
  </figure>
  <p>Le counterpick en top vaut environ {n(cp['top'])} golds à 15 minutes, soit un ou deux sbires. En jungle et en mid, une quinzaine de golds. En bot et en support, rien de mesurable.</p>
  <figure>
    <div class="ftitle">Le tilt en Bo3/Bo5 existe-t-il&nbsp;?</div>
    <div id="f-tilt"></div>
    <figcaption>Écart entre le winrate réel de l'équipe qui vient de perdre et celui prévu par l'Elo, en points. Barres = ±2 erreurs-types.</figcaption>
  </figure>
  <p>L'équipe qui perd une game fait {n(-t_same['ecart_pts'],1)} points de moins que prévu à la game suivante. On dirait du tilt. Mais le placebo trahit l'effet : à la rencontre suivante des mêmes équipes, des semaines plus tard, l'écart est encore plus grand ({sgn(t_next['ecart_pts'],1)}). Ce n'est pas du tilt, c'est l'Elo qui sous-estime l'écart entre les deux équipes.</p>
</div></section>

<section><div class="col">
  <span class="eyebrow">Limites</span>
  <h2>Ce que ce modèle ne sait pas</h2>
  <ul class="changes">
    <li><span class="tag bug">Équipe</span><span>Un joueur qui n'a jamais joué sans ses quatre coéquipiers ne peut pas être séparé d'eux.</span></li>
    <li><span class="tag bug">Données</span><span>Pas de fichiers 2023-2024 complets (Google Drive bloque leur téléchargement pour l'instant) : le modèle ne connaît que 2025-2026, plus 2022 pour les bonus.</span></li>
    <li><span class="tag bug">Échelle</span><span>Les écarts entre ligues qui ne se rencontrent jamais sont extrapolés. Les « points » sont une échelle linéaire, pas des golds réels quand on compare la LCK et une ligue régionale.</span></li>
    <li><span class="tag bug">Aveu</span><span>J'ai regardé février 2026 une fois au début, pour les modèles de référence. Tous les réglages ont ensuite été faits sur janvier 2026, puis sur août-septembre pour le multivers.</span></li>
  </ul>
</div></section>

<footer class="col">
  <p>Code : Python (pandas, NumPy, SciPy, scikit-learn). Données : <a href="https://oracleselixir.com/tools/downloads">Oracle's Elixir</a>, match data 2022, 2025 et 2026 (jusqu'au {frdate(D['data_until'])}). Méthode inspirée de B.A.S.I.C. (HQEye). Notes = ridge « RAPM » sur l'écart d'or, prior « stats » appris par rôle, niveaux de ligue portés par les joueurs.</p>
</footer>
</div>
<div class="tip" id="tip"></div>
'''

JS=r'''
<script id="data" type="application/json">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);
const $=s=>document.querySelector(s);
const fmt=(x,d=0)=>Number(x).toLocaleString('fr-FR',{minimumFractionDigits:d,maximumFractionDigits:d});
const pct=(x,d=0)=>fmt(x*100,d)+' %';
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const tip=$('#tip');
function showTip(e,h){tip.innerHTML=h;tip.style.opacity=1;tip.style.left=Math.min(e.clientX+14,innerWidth-270)+'px';tip.style.top=(e.clientY+14)+'px'}
function hideTip(){tip.style.opacity=0}
function table(el,cols,rows,hl){
  el.innerHTML='<thead><tr>'+cols.map(c=>`<th class="${c.r?'r':''}">${c.h}</th>`).join('')+'</tr></thead><tbody>'+
  rows.map((r,i)=>`<tr class="${hl&&hl(r,i)?'hl':''}">`+cols.map(c=>`<td class="${c.r?'r':''}">${c.f?c.f(r,i):esc(r[c.k])}</td>`).join('')+'</tr>').join('')+'</tbody>';
}
const ideas=[
 ['Quête principale','Une note joueur qui sépare le joueur de son équipe, de son champion et de sa ligue, jugée sur sa capacité à prédire la saison suivante.'],
 ['Sonde → bonus','Combien d\'or rapporte vraiment un counterpick ? (ordre de draft reconstitué pick par pick)'],
 ['Sonde → bonus','Le tilt existe-t-il en Bo3/Bo5, et survit-il à un placebo ?'],
 ['Intégrée','Scouting : le modèle aurait-il repéré les joueurs d\'ERL et d\'académie promus en 2026 ?'],
 ['Plus tard','Le Fearless draft coûte-t-il des games aux équipes à petit champion pool ? Il faut 2024 pour comparer.'],
 ['Écartée','Le joueur le plus « moyen » de LoL : trop proche de la vidéo.'],
 ['Écartée','Les comebacks par région : déjà beaucoup traité.']];
$('#ideas').innerHTML=ideas.map(([s,t])=>`<li><span class="pill">${s}</span><span>${t}</span></li>`).join('');
table($('#t-v01'),[{h:'Joueur',k:'name'},{h:'Équipe',k:'team'},{h:'Ligue',k:'league'},{h:'Rôle',k:'role'},{h:'Games',k:'GP',r:1},{h:'KDA',r:1,f:r=>fmt(r.KDA,2)},{h:'Winrate',r:1,f:r=>pct(r.W)}],D.v01,(r,i)=>i==0);
table($('#t-v02'),[{h:'Joueur',k:'name'},{h:'Équipe',k:'team'},{h:'Ligue',k:'league'},{h:'Rôle',k:'role'},{h:'Score',r:1,f:r=>fmt(r.v02,2)}],D.v02,(r,i)=>i==0);
{const want={Top:{DPM:.20,DMG:.15,GD10:.15,CSD10:.10,XPD10:.10,KP:.15,KDA:.10,TDPG:.05},Mid:{DPM:.25,DMG:.20,GD10:.15,CSD10:.10,KP:.15,KDA:.10,FB:.05},ADC:{DPM:.25,DMG:.25,KDA:.15,CSPM:.15,CSD10:.10,GD10:.10}};
 const rows=[];for(const r of ['ADC','Mid','Top'])for(const s of Object.keys(want[r])){const w=want[r][s],e=D.v02_eff[r][s];if(Math.abs(e-w)>=.05)rows.push({r,s,w,e})}
 table($('#t-eff'),[{h:'Rôle',k:'r'},{h:'Stat',k:'s'},{h:'Poids voulu ⇒ appliqué',f:x=>`${fmt(x.w,2)} <span class="arrow">⇒</span> <b style="color:var(${x.e>x.w?'--buff':'--nerf'})">${fmt(x.e,2)}</b>`}],rows);}
const NS='http://www.w3.org/2000/svg';
function el(t,a,p){const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);if(p)p.appendChild(e);return e}
function hbar(host,items,o){
  const W=Math.max(280,Math.min(host.clientWidth||640,900)),stack=W<520,row=(o.row||24)+(stack?16:0),L=stack?14:(o.left||130),R=stack?Math.min(o.right||56,96):(o.right||56),T=8,B=28;
  const H=T+B+row*items.length;const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,width:'100%',role:'img','aria-label':o.aria||''});
  const mn=o.min,mx=o.max,x=v=>L+(Math.max(mn,Math.min(mx,v))-mn)/(mx-mn)*(W-L-R);
  const g=el('g',{class:'grid'},svg),ax=el('g',{class:'axis'},svg);
  for(const t of o.ticks){el('line',{x1:x(t),x2:x(t),y1:T,y2:H-B+4},g);const tx=el('text',{x:x(t),y:H-B+18,'text-anchor':'middle'},ax);tx.textContent=o.tf?o.tf(t):t}
  const base=o.base??0;
  items.forEach((d,i)=>{const y0=T+i*row,y=stack?y0+16:y0,h=(stack?row-16:row)-8;
    const lb=stack?el('text',{x:L-8,y:y0+12,'text-anchor':'start','font-size':12,'font-weight':d.hl?600:400},svg):el('text',{x:L-8,y:y+h/2+4,'text-anchor':'end','font-size':12.5,'font-weight':d.hl?600:400},svg);lb.textContent=d.label;
    el('rect',{x:Math.min(x(base),x(d.value)),y:y+2,width:Math.max(1,Math.abs(x(d.value)-x(base))),height:h-2,rx:2,fill:d.hl?'var(--gold)':(d.neg&&d.value<base?'var(--div-neg)':'var(--teal)')},svg);
    if(d.lo!=null){el('line',{x1:x(d.lo),x2:x(d.hi),y1:y+h/2+1,y2:y+h/2+1,stroke:'var(--ink)','stroke-width':1.5},svg);for(const v of [d.lo,d.hi])el('line',{x1:x(v),x2:x(v),y1:y+h/2-4,y2:y+h/2+6,stroke:'var(--ink)','stroke-width':1.5},svg)}
    if(o.vf){const right=d.value>=base;const vx=right?Math.max(x(d.value),d.hi!=null?x(d.hi):0)+6:Math.min(x(d.value),d.lo!=null?x(d.lo):1e9)-6;
      const vt=el('text',{x:vx,y:y+h/2+4,'font-size':12,'text-anchor':right?'start':'end',fill:'var(--muted)','font-family':'var(--mono)'},svg);vt.textContent=o.vf(d)}
    const hit=el('rect',{x:0,y:y0,width:W,height:row,fill:'transparent'},svg);
    hit.addEventListener('mousemove',e=>showTip(e,d.tip||`${esc(d.label)} : ${o.vf?o.vf(d):d.value}`));hit.addEventListener('mouseleave',hideTip);
  });
  el('line',{x1:x(base),x2:x(base),y1:T,y2:H-B+4,stroke:'var(--muted)','stroke-width':1},svg);
  host.innerHTML='';host.appendChild(svg);
}
function lines(host,series,cats,o){
  const W=Math.max(300,Math.min(host.clientWidth||640,900)),H=260,L=44,R=96,T=12,B=30;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,width:'100%',role:'img','aria-label':o.aria});
  const x=i=>L+i*(W-L-R)/(cats.length-1),y=v=>T+(o.max-v)/(o.max-o.min)*(H-T-B);
  const g=el('g',{class:'grid'},svg),ax=el('g',{class:'axis'},svg);
  for(const t of o.ticks){el('line',{x1:L,x2:W-R,y1:y(t),y2:y(t)},g);const tx=el('text',{x:L-8,y:y(t)+4,'text-anchor':'end'},ax);tx.textContent=fmt(t,2)}
  cats.forEach((c,i)=>{const tx=el('text',{x:x(i),y:H-B+18,'text-anchor':'middle'},ax);tx.textContent=W<480?(c.s??c.full[0]):c.label});
  series.forEach(s=>{el('path',{d:s.v.map((v,i)=>(i?'L':'M')+x(i)+' '+y(v)).join(''),fill:'none',stroke:s.color,'stroke-width':2,'stroke-linejoin':'round'},svg);
    s.v.forEach((v,i)=>el('circle',{cx:x(i),cy:y(v),r:3.5,fill:s.color,stroke:'var(--surface)','stroke-width':1.5},svg));
    const lt=el('text',{x:W-R+8,y:y(s.v[s.v.length-1])+4+(s.dy||0),'font-size':12,'font-weight':600},svg);lt.textContent=s.name});
  const hl=el('line',{x1:0,x2:0,y1:T,y2:H-B,stroke:'var(--muted)','stroke-width':1,opacity:0},svg);
  cats.forEach((c,i)=>{const hit=el('rect',{x:x(i)-(W-L-R)/(cats.length-1)/2,y:T,width:(W-L-R)/(cats.length-1),height:H-T-B,fill:'transparent'},svg);
    hit.addEventListener('mousemove',e=>{hl.setAttribute('x1',x(i));hl.setAttribute('x2',x(i));hl.setAttribute('opacity',1);showTip(e,`<b>${c.full}</b><br>`+series.map(s=>`${esc(s.name)} : ${fmt(s.v[i],3)}`).join('<br>'))});
    hit.addEventListener('mouseleave',()=>{hl.setAttribute('opacity',0);hideTip()})});
  host.innerHTML='';host.appendChild(svg);
}
function draw(){
  const MAJ=new Set(['LCK','LPL','LEC','LCS','CBLOL','LCP']);
  const lg=Object.entries(D.leagues_now).map(([k,v])=>({label:k,value:v,hl:MAJ.has(k),neg:true,tip:`<b>${esc(k)}</b><br>${fmt(v)} points${MAJ.has(k)?' · ligue majeure':''}`}));
  const lmin=Math.min(...lg.map(d=>d.value)),lmax=Math.max(...lg.map(d=>d.value));
  hbar($('#f-leagues'),lg,{left:84,right:52,row:20,ticks:[-800,-400,0,400,800].filter(t=>t>=lmin-100&&t<=lmax+100),min:Math.floor((lmin-150)/100)*100,max:Math.ceil((lmax+100)/100)*100,vf:d=>(d.value>0?'+':'')+fmt(d.value),aria:'Niveau des ligues'});
  const F=D.final;const names=['Pile ou face (+ côté bleu)','Elo équipe','Elo porté par les joueurs','v0.1 KDA','v0.3 LoL Ratings 2.0 (corrigé par rôle)','v0.4 RAPM brut','v0.5 RAPM + ligues','v1.0 LoL Ratings 3.0'];
  const lab={'Pile ou face (+ côté bleu)':'Hasard (+ côté bleu)','v0.3 LoL Ratings 2.0 (corrigé par rôle)':'v0.3 Ratings 2.0 corrigé'};
  hbar($('#f-final'),names.map(k=>({label:lab[k]||k,value:F[k].auc,hl:k.startsWith('v1.0'),acc:F[k].acc,tip:`<b>${esc(lab[k]||k)}</b><br>AUC ${fmt(F[k].auc,3)} · ${pct(F[k].acc,1)} de bonnes prédictions`})),
    {left:188,right:112,row:26,base:.5,min:.5,max:.74,ticks:[.5,.55,.6,.65,.7],tf:t=>fmt(t,2),vf:d=>`${fmt(d.value,3)} (${pct(d.acc,0)})`,aria:'AUC février 2026'});
  const R=D.rolling.total;const rn=['KDA à date','v1.0 (2025 seul, gelée)','Elo équipe (mis à jour à chaque game)','Elo joueurs (mis à jour à chaque game)','v1.1 ré-entraînée chaque mois','v1.2 + Elo (combinés)','v1.2 rattachement mixte'];
  const rl={'KDA à date':'KDA (mis à jour chaque mois)','v1.0 (2025 seul, gelée)':'v1.0 gelée (notes 2025)','Elo équipe (mis à jour à chaque game)':'Elo équipe (chaque game)','Elo joueurs (mis à jour à chaque game)':'Elo joueurs (chaque game)','v1.1 ré-entraînée chaque mois':'v1.1 (chaque mois)','v1.2 + Elo (combinés)':'v1.2 + Elo combinés','v1.2 rattachement mixte':'v1.2 (chaque mois)'};
  hbar($('#f-rolling'),rn.map(k=>({label:rl[k],value:R[k].auc,lo:R[k].auc_lo,hi:R[k].auc_hi,acc:R[k].acc,hl:k==='v1.2 rattachement mixte',tip:`<b>${esc(rl[k])}</b><br>AUC ${fmt(R[k].auc,3)} [${fmt(R[k].auc_lo,3)} – ${fmt(R[k].auc_hi,3)}]<br>${pct(R[k].acc,1)} de bonnes prédictions`})),
    {left:200,right:100,row:28,base:.5,min:.5,max:.76,ticks:[.5,.55,.6,.65,.7,.75],tf:t=>fmt(t,2),vf:d=>`${fmt(d.value,3)} (${pct(d.acc,1)})`,aria:'AUC saison 2026'});
  const M=D.rolling.monthly,MN=['févr.','mars','avr.','mai','juin','juil.','août','sept.'],FULL=['Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre'];
  const keys=Object.keys(M['v1.2 rattachement mixte']);const cats=keys.map((k,i)=>({label:MN[i],full:FULL[i]+' 2026'}));
  const ser=[['v1.2','v1.2 rattachement mixte','var(--s1)',0],['Elo équipe','Elo équipe (mis à jour à chaque game)','var(--s2)',0],['v1.0 gelée','v1.0 (2025 seul, gelée)','var(--s3)',0]]
    .map(([name,k,color])=>({name,color,v:keys.map(m=>M[k][m].auc)}));
  const ends=ser.map(s=>s.v[s.v.length-1]);ser.forEach((s,i)=>{for(let j=0;j<i;j++)if(Math.abs(ends[i]-ends[j])<.012)s.dy=(s.dy||0)+(ends[i]<ends[j]?12:-12)});
  const all=ser.flatMap(s=>s.v);lines($('#f-monthly'),ser,cats,{min:Math.floor(Math.min(...all)*50)/50-.01,max:Math.ceil(Math.max(...all)*50)/50,ticks:[.6,.65,.7,.75].filter(t=>t>=Math.min(...all)-.02&&t<=Math.max(...all)+.02),aria:'AUC par mois'});
  {const R=D.calib.reliability['v1.2'].filter(r=>r.n>=50);const cats=R.map(r=>({label:fmt(r.pred*100,0)+' %',s:fmt(r.pred*100,0),full:`Annoncé ${fmt(r.pred*100,0)} % · ${fmt(r.n)} games`}));
   lines($('#f-calib'),[{name:'Réel',color:'var(--s1)',v:R.map(r=>r.obs)},{name:'Diagonale',color:'var(--muted)',v:R.map(r=>r.pred),dy:14}],cats,{min:0,max:1,ticks:[0,.25,.5,.75,1],aria:'Calibration'});}
  const S=D.scouting.auc;const sl=[['theta','v1.0 (note mondiale)'],['v03','v0.3 Ratings 2.0 corrigé'],['KDA','KDA'],['W','Winrate'],['u','v1.0 écart intra-ligue']];
  hbar($('#f-scout'),sl.map(([k,l])=>({label:l,value:S[k],hl:k==='theta'})),{left:160,right:44,row:24,base:.5,min:.5,max:.85,ticks:[.5,.6,.7,.8],tf:t=>fmt(t,1),vf:d=>fmt(d.value,2),aria:'AUC promotions'});
  const C=D.counter,RN={top:'Top',jng:'Jungle',mid:'Mid',bot:'ADC',sup:'Support'};
  hbar($('#f-counter'),Object.keys(RN).map(k=>{const v=C[k].champ/2,se=C[k].champ_se/2;return{label:RN[k],value:v,lo:v-2*se,hi:v+2*se,neg:true,tip:`<b>${RN[k]}</b> : ${v>0?'+':''}${fmt(v)} golds à 15 min (± ${fmt(2*se)})`}}),
    {left:70,right:56,row:30,min:-40,max:65,ticks:[-40,-20,0,20,40,60],vf:d=>(d.value>0?'+':'')+fmt(d.value)+' g',aria:'Valeur du counterpick'});
  const TL={'même série (quelques minutes après)':'Game suivante (même série)','prochaine rencontre (<60 j)':'Rencontre suivante (< 60 j)','prochaine rencontre (>60 j)':'Rencontre suivante (> 60 j)'};
  hbar($('#f-tilt'),D.tilt.map(t=>({label:TL[t.kind],value:t.ecart_pts,lo:t.ecart_pts-2*t.se_pts,hi:t.ecart_pts+2*t.se_pts,neg:true,tip:`<b>${esc(TL[t.kind])}</b><br>${fmt(t.win*100,1)} % réel vs ${fmt(t.exp*100,1)} % prévu (${fmt(t.n)} games)`})),
    {left:190,right:30,row:32,min:-7,max:1,ticks:[-6,-4,-2,0],vf:d=>fmt(d.value,1)+' pt',aria:'Tilt'});
}
{const W=D.prior_w,roles=['Top','Jungle','Mid','ADC','Support'];
 const lab={kpm:'Kills / min',dthpm:'Morts / min',apm:'Assists / min',dpm:'Dégâts / min',damageshare:'Part des dégâts',damagetakenperminute:'Dégâts subis / min','earned gpm':'Or gagné / min',earnedgoldshare:'Part de l\'or de l\'équipe',cspm:'CS / min',vspm:'Score de vision / min',wpm:'Wards posées / min',wcpm:'Wards détruites / min',cwpm:'Pinks / min',kp:'Kill participation',ttpm:'Dégâts aux tours / min',golddiffat15:'Écart d\'or à 15',xpdiffat15:'Écart d\'XP à 15',csdiffat15:'Écart de CS à 15'};
 const stats=Object.keys(W.Top).filter(s=>s!=='has_lane');const mx=1200;
 const col=v=>{const t=Math.min(1,Math.abs(v)/mx);return `color-mix(in oklab, var(${v>=0?'--div-pos':'--div-neg'}) ${Math.round(t*100)}%, var(--div-mid))`};
 let h='<table style="width:auto;min-width:100%"><thead><tr><th>Stat</th>'+roles.map(r=>`<th class="r">${r}</th>`).join('')+'</tr></thead><tbody>';
 for(const s of stats){h+=`<tr><td>${lab[s]||s}</td>`+roles.map(r=>{const v=W[r][s];const strong=Math.abs(v)>600;return `<td class="r" style="background:${col(v)};${strong?'color:#fff;font-weight:600':''}">${v>0?'+':''}${fmt(v)}</td>`}).join('')+'</tr>'}
 $('#f-heat').innerHTML=h+'</tbody></table>';}
{const WT=D.worlds.teams,A=D.worlds.a,B=D.worlds.b;
 const sig=z=>1/(1+Math.exp(-z)),pg=(sa,sb)=>0.5*(sig(A+B*(sa-sb))+1-sig(A+B*(sb-sa)));
 const pser=(p,n)=>{let s=0,c=1;for(let j=0;j<n;j++){if(j>0)c=c*(n-1+j)/j;s+=c*Math.pow(p,n)*Math.pow(1-p,j)}return s};
 const top=WT.slice(0,24),T0=WT[0];
 table($('#t-worlds'),[{h:'#',r:1,f:(r,i)=>i+1},{h:'Équipe',f:r=>`<b>${esc(r.team)}</b>`},{h:'Ligue',f:r=>esc(r.league)},{h:'Titulaires',f:r=>`<span class="lineup">${r.lineup.map(esc).join(' · ')}</span>`},{h:'Force',r:1,f:r=>fmt(r.pts)},
   {h:`Game vs ${esc(T0.team)}`,r:1,f:r=>r===T0?'–':pct(pg(r.s,T0.s))},{h:`Bo5 vs ${esc(T0.team)}`,r:1,f:r=>r===T0?'–':pct(pser(pg(r.s,T0.s),3))}],top,(r,i)=>i==0);
 const opts=WT.map((t,i)=>`<option value="${i}">${esc(t.team)} (${esc(t.league)})</option>`).join('');
 $('#w-a').innerHTML=opts;$('#w-b').innerHTML=opts;$('#w-a').value=0;$('#w-b').value=Math.min(2,WT.length-1);
 const upd=()=>{const a=WT[+$('#w-a').value],b=WT[+$('#w-b').value];if(a===b){$('#w-out').textContent='Choisis deux équipes différentes.';return}
   const p=pg(a.s,b.s);$('#w-out').innerHTML=`<b>${esc(a.team)}</b> bat <b>${esc(b.team)}</b> : ${pct(p)} sur une game · ${pct(pser(p,2))} en Bo3 · ${pct(pser(p,3))} en Bo5`};
 $('#w-a').addEventListener('change',upd);$('#w-b').addEventListener('change',upd);upd();}
{const S={season:'2026',view:'P',tier:'M',region:'',league:'',comp:'',role:'',path:'',sort:'p',unit:'pts',min:20,minc:5,q:'',shown:25,open:null,cmp:[]};
 try{Object.assign(S,JSON.parse(localStorage.getItem('lr3-explorer2')||'{}'),{shown:25,open:null,q:'',cmp:[]})}catch(e){}
 if(!D.seasons[S.season])S.season='2026'; if(!['M','2','3'].includes(S.tier))S.tier='M';
 const save=()=>{try{const {season,view,tier,region,league,comp,role,path,sort,unit,min,minc}=S;localStorage.setItem('lr3-explorer2',JSON.stringify({season,view,tier,region,league,comp,role,path,sort,unit,min,minc}))}catch(e){}};
 const SD=()=>D.seasons[S.season];
 let BYP={};
 function index(){BYP={};const dl=SD().deltas;for(const c in dl)for(const e of dl[c]){(BYP[e[0]]=BYP[e[0]]||[]).push([c,e])}}
 const U=v=>S.unit==='gold'?v*5:v, US=()=>S.unit==='gold'?' g':'';
 const MN=['janv.','févr.','mars','avr.','mai','juin','juil.','août','sept.','oct.','nov.','déc.'];
 const mlab=k=>k.length===7?MN[+k.slice(5)-1]:'fin';
 const cmode=()=>S.view==='P'&&!!S.comp;
 const SORTS={season:[['p','Note'],['u','Écart au rôle de sa ligue'],['m1','N°1 multivers'],['gp','Games']],comp:[['p','Note sur la compétition'],['d','Écart avec sa saison'],['w','Victoires'],['k','KDA'],['gp','Games']]};
 function fillSelects(){
   const sd=SD(),LM=sd.league_meta,LV=sd.levels,CP=sd.comps;
   const regs=[...new Set(Object.values(LM).filter(m=>m.tier===S.tier).map(m=>m.region))].sort();
   if(S.region&&!regs.includes(S.region))S.region='';
   $('#x-region').innerHTML='<option value="">Toutes</option>'+regs.map(r=>`<option ${r===S.region?'selected':''}>${esc(r)}</option>`).join('');
   const lgs=Object.entries(LM).filter(([k,m])=>m.tier===S.tier&&(!S.region||m.region===S.region)).sort((a,b)=>(LV[b[0]]??-1e9)-(LV[a[0]]??-1e9));
   if(S.league&&!lgs.some(([k])=>k===S.league))S.league='';
   $('#x-league').innerHTML='<option value="">Toutes</option>'+lgs.map(([k,m])=>`<option value="${esc(k)}" ${k===S.league?'selected':''}>${esc(k)} · ${esc(m.desc)}</option>`).join('');
   const cps=Object.entries(CP).filter(([k,c])=>c.tier===S.tier&&(c.region==='International'||!S.region||c.region===S.region)&&(!S.league||c.league===S.league||c.cup)).sort((a,b)=>(!!a[1].cup-!!b[1].cup)||b[1].games-a[1].games);
   if(S.comp&&!cps.some(([k])=>k===S.comp))S.comp='';
   const opt=([k,c])=>`<option value="${esc(k)}" ${k===S.comp?'selected':''}>${esc(c.label)} (${c.n} joueurs)</option>`;
   const cu=cps.filter(x=>x[1].cup),lg=cps.filter(x=>!x[1].cup).sort((a,b)=>((LV[b[1].league]??-1e9)-(LV[a[1].league]??-1e9))||a[1].label.localeCompare(b[1].label,'fr'));
   $('#x-comp').innerHTML='<option value="">Toute la saison</option>'+(lg.length?`<optgroup label="Ligues">${lg.map(opt).join('')}</optgroup>`:'')+(cu.length?`<optgroup label="Tournois entre ligues">${cu.map(opt).join('')}</optgroup>`:'');
   const so=SORTS[cmode()?'comp':'season'];if(!so.some(o=>o[0]===S.sort))S.sort='p';
   $('#x-sort').innerHTML=so.map(([v,l])=>`<option value="${v}" ${v===S.sort?'selected':''}>${l}</option>`).join('');
   const mn=$('#x-min');if(cmode()){mn.min=3;mn.max=40;mn.step=1;mn.value=S.minc;$('#x-min-v').textContent=S.minc;$('#x-min-l').textContent='Games min. (compétition)'}else{mn.min=10;mn.max=120;mn.step=5;mn.value=S.min;$('#x-min-v').textContent=S.min;$('#x-min-l').textContent='Games min. (saison)'}
   $('#x-role').value=S.role;$('#x-path').value=S.path;$('#x-unit').value=S.unit;$('#x-q').value=S.q;
   for(const [id,k] of [['#x-season','season'],['#x-view','view'],['#x-tier','tier']])document.querySelectorAll(id+' button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.v===S[k]));
   document.querySelectorAll('.controls .p-only').forEach(l=>l.hidden=S.view!=='P');
   $('#x-legend-P').hidden=S.view!=='P';$('#x-legend-T').hidden=S.view!=='T';
 }
 function spark(vals,months){
   const pts=vals.map((v,i)=>[i,v]).filter(d=>d[1]!=null);if(pts.length<2)return '<span class="muted">Pas assez de données dans la saison.</span>';
   const W=320,H=90,L=36,R=10,T=10,B=22,xs=i=>L+i*(W-L-R)/(vals.length-1);const lo=Math.min(...pts.map(d=>d[1])),hi=Math.max(...pts.map(d=>d[1]));
   const pad=Math.max(40,(hi-lo)*.15),mn=lo-pad,mx=hi+pad,ys=v=>T+(mx-v)/(mx-mn)*(H-T-B);
   const path=pts.map((d,k)=>(k?'L':'M')+xs(d[0]).toFixed(1)+' '+ys(d[1]).toFixed(1)).join('');
   const dots=pts.map(d=>`<circle cx="${xs(d[0]).toFixed(1)}" cy="${ys(d[1]).toFixed(1)}" r="3" fill="var(--gold)"><title>${mlab(months[d[0]])} : ${fmt(U(d[1]))}${US()}</title></circle>`).join('');
   const labs=[0,Math.floor((vals.length-1)/2),vals.length-1].map(i=>`<text x="${xs(i)}" y="${H-6}" text-anchor="middle" font-size="10" fill="var(--muted)" font-family="var(--mono)">${mlab(months[i])}</text>`).join('');
   const yl=[lo,hi].map(v=>`<text x="${L-6}" y="${ys(v)+3}" text-anchor="end" font-size="10" fill="var(--muted)" font-family="var(--mono)">${fmt(U(v))}</text>`).join('');
   return `<svg viewBox="0 0 ${W} ${H}" width="${W}" style="max-width:100%" role="img" aria-label="Évolution de la note"><path d="${path}" fill="none" stroke="var(--gold)" stroke-width="2"/>${dots}${labs}${yl}</svg>`;
 }
 function card(p,pi){
   const sd=SD(),LM=sd.league_meta;const tags={new:'Nouveau cette saison',moved:'A changé de ligue',up:'Promu en ligue majeure',down:'Redescendu'};
   const fl=(p.fl||[]).map(f=>`<span class="pill">${tags[f]}</span>`).join(' ');
   const tr=p.id!=null?sd.traj[p.id]:[];
   const comps=(BYP[pi]||[]).sort((a,b)=>b[1][1]-a[1][1]).map(([c,e])=>`<tr><td>${esc(sd.comps[c].label)}</td><td class="r">${e[1]}</td><td class="r">${pct(e[2])}</td><td class="r">${fmt(e[3],1)}</td><td class="r">${fmt(U(p.p+e[4]))}${US()} <span class="muted hide-sm">(${e[4]>0?'+':''}${fmt(U(e[4]))})</span></td></tr>`).join('');
   return `<div class="pcard"><div class="pcard-main"><div><b>${esc(p.n)}</b> · ${esc(p.r)} · ${esc(p.t)} (${esc(p.l)}, ${esc(LM[p.l]?.desc||'')}) ${fl}</div>
     <div class="muted">${esc(p.c||'')}</div>
     <div>Saison ${S.season} : note ${fmt(U(p.p))}${US()} ± ${fmt(U(p.sd))} sur ${p.gp} games · N°1 multivers ${p.m1==null?'–':pct(p.m1)} · top 5 ${p.m5==null?'–':pct(p.m5)}</div>
     <div><button type="button" class="x-cmp-btn" data-k="${S.season}|${pi}">${S.cmp.includes(S.season+'|'+pi)?'Retirer de la comparaison':'Comparer avec d\'autres joueurs'}</button></div>
     ${p.rs>=0.8?`<div class="muted">Mêmes quatre coéquipiers dans ${pct(p.rs)} de ses games : sa note se sépare mal de celle de son équipe.</div>`:''}
     ${comps?`<table class="mini"><thead><tr><th>Compétition</th><th class="r">Games</th><th class="r">Vict.</th><th class="r">KDA</th><th class="r">Note</th></tr></thead><tbody>${comps}</tbody></table>`:''}</div>
     <div class="pcard-chart"><div class="muted" style="font-size:12px">Note au 1<sup>er</sup> de chaque mois (modèle ré-entraîné sur les games de la saison déjà jouées)</div>${spark(tr,sd.traj_months)}</div></div>`;
 }
 function rowsHTML(cols,rows,hl){
   return '<thead><tr>'+cols.map(c=>`<th class="${c.r?'r':''}">${c.h}</th>`).join('')+'</tr></thead><tbody>'+
     rows.map((r,i)=>{const key=S.season+'|'+r._i;const op=S.open===key;
       return `<tr class="prow ${hl(r,i)?'hl':''}" tabindex="0" role="button" aria-expanded="${op}" data-k="${esc(key)}">`+cols.map(c=>`<td class="${c.r?'r':''}">${c.f(r,i)}</td>`).join('')+'</tr>'+(op?`<tr class="pdetail"><td colspan="${cols.length}">${card(r,r._i)}</td></tr>`:'')}).join('')+'</tbody>';
 }
 function renderPlayers(){
   const sd=SD(),P=sd.players,LM=sd.league_meta,LV=sd.levels;const q=S.q.trim().toLowerCase();
   const base=p=>(!S.region||LM[p.l]?.region===S.region)&&(!S.league||p.l===S.league)&&(!S.role||p.r===S.role)&&(!S.path||(p.fl||[]).includes(S.path))&&(!q||p.n.toLowerCase().includes(q)||p.t.toLowerCase().includes(q));
   const pname=r=>`<b>${esc(r.n)}</b>${(r.fl||[]).includes('up')?' <span class="pill">promu</span>':(r.fl||[]).includes('new')?' <span class="pill">nouveau</span>':''}`;
   let rows,cols,total,info;
   if(!cmode()){
     rows=P.map((p,i)=>Object.assign({_i:i},p)).filter(p=>p.g===S.tier&&p.gp>=S.min&&base(p));
     const key={p:x=>x.p,u:x=>x.u??-1e9,m1:x=>x.m1??-1,gp:x=>x.gp}[S.sort];rows.sort((a,b)=>key(b)-key(a)||b.p-a.p);
     cols=[{h:'#',r:1,f:(r,i)=>i+1},{h:'Joueur',f:pname},{h:'Équipe',f:r=>esc(r.t)},{h:'Ligue',f:r=>`<span title="${esc(LM[r.l]?.desc||'')}">${esc(r.l)}</span>`},{h:'Poste',f:r=>r.r},{h:'Games',r:1,f:r=>r.gp},
       {h:S.unit==='gold'?'Note (golds)':'Note',r:1,f:r=>`${fmt(U(r.p))} <span class="muted">± ${fmt(U(r.sd))}</span>`},{h:'vs rôle',r:1,f:r=>r.u==null?'–':(r.u>0?'+':'')+fmt(r.u)+' g'},
       {h:'N°1 multivers',r:1,f:r=>r.m1==null?'<span class="muted">–</span>':r.m1>0?pct(r.m1):'<span class="muted">0 %</span>'}];
     total=rows.length;info=`${fmt(total)} joueur${total>1?'s':''} · saison ${S.season}`;
     if(S.league){const m=LM[S.league];info+=` · ${S.league} (${m.desc}) : niveau de la ligue ${LV[S.league]!=null?(LV[S.league]>0?'+':'')+fmt(U(LV[S.league]))+US():'n.c.'}${S.unit==='pts'?' points':''}`}
   }else{
     const c=sd.comps[S.comp];
     rows=(sd.deltas[S.comp]||[]).map(e=>Object.assign({_i:e[0],cg:e[1],cw:e[2],ck:e[3],cd:e[4],cs:e[5]},P[e[0]])).filter(p=>p.cg>=S.minc&&base(p));
     const key={p:x=>x.p+x.cd,d:x=>x.cd,w:x=>x.cw,k:x=>x.ck,gp:x=>x.cg}[S.sort];rows.sort((a,b)=>key(b)-key(a)||(b.p+b.cd)-(a.p+a.cd));
     cols=[{h:'#',r:1,f:(r,i)=>i+1},{h:'Joueur',f:pname},{h:'Équipe',f:r=>esc(r.t)},{h:'Ligue',f:r=>`<span title="${esc(LM[r.l]?.desc||'')}">${esc(r.l)}</span>`},{h:'Poste',f:r=>r.r},{h:'Games',r:1,f:r=>r.cg},{h:'Victoires',r:1,f:r=>pct(r.cw)},{h:'KDA',r:1,f:r=>fmt(r.ck,1)},
       {h:S.unit==='gold'?'Note compétition (golds)':'Note compétition',r:1,f:r=>`${fmt(U(r.p+r.cd))} <span class="muted">± ${fmt(U(Math.hypot(r.sd,r.cs)))}</span>`},
       {h:'Écart avec sa saison',r:1,f:r=>{const v=U(r.cd),t=S.unit==='gold'?50:10;return Math.abs(v)<t?`<span class="muted">= ${v>0?'+':''}${fmt(v)}</span>`:`<span style="color:var(${v>0?'--buff':'--nerf'})">${v>0?'▲ +':'▼ '}${fmt(v)}</span>`}},
       {h:'Note saison',r:1,f:r=>`<span class="muted">${fmt(U(r.p))}</span>`}];
     total=rows.length;info=`${fmt(total)} joueur${total>1?'s':''} · ${c.label} (${c.games} games)`;
   }
   rows=rows.slice(0,S.shown);
   $('#x-info').textContent=info+(!total&&S.path==='up'&&S.tier!=='M'?' · les promus jouent en ligue majeure : passe sur « Ligues majeures »':'');
   $('#x-table').innerHTML=rowsHTML(cols,rows,(r,i)=>i==0&&S.sort==='p'&&!q);
   const mb=$('#x-more');mb.hidden=total<=S.shown;mb.textContent=`Afficher ${Math.min(25,total-S.shown)} de plus (${fmt(total-S.shown)} restants)`;
 }
 function renderTeams(){
   const sd=SD(),LM=sd.league_meta;const q=S.q.trim().toLowerCase();
   let rows=sd.teams.filter(t=>LM[t.league]&&LM[t.league].tier===S.tier&&(!S.region||LM[t.league].region===S.region)&&(!S.league||t.league===S.league)&&(!q||t.team.toLowerCase().includes(q)||t.lineup.some(x=>x.n.toLowerCase().includes(q))));
   rows.sort((a,b)=>b.pts-a.pts);const total=rows.length;rows=rows.slice(0,S.shown);
   $('#x-info').textContent=`${fmt(total)} équipe${total>1?'s':''} · saison ${S.season}`+(S.league?` · ${S.league} (${LM[S.league].desc})`:'');
   table($('#x-table'),[{h:'#',r:1,f:(r,i)=>i+1},{h:'Équipe',f:r=>`<b>${esc(r.team)}</b>`},{h:'Ligue',f:r=>esc(r.league)},{h:'Effectif',f:r=>`<span class="lineup">${r.lineup.map(x=>`<span title="${x.r}">${esc(x.n)}</span>`).join(' · ')}</span>`},
     {h:S.unit==='gold'?'Force (golds)':'Force',r:1,f:r=>fmt(U(r.pts))},{h:"Contre l'équipe moyenne",r:1,f:r=>pct(r.p_vs_avg)},{h:'Bilan de la saison',r:1,f:r=>r.wr==null?'–':`${pct(r.wr)} <span class="muted">(${r.gp} g)</span>`}],rows,(r,i)=>i==0&&!q);
   const mb=$('#x-more');mb.hidden=total<=S.shown;mb.textContent=`Afficher ${Math.min(25,total-S.shown)} de plus (${fmt(total-S.shown)} restantes)`;
 }
 const erf=x=>{const t=1/(1+0.3275911*Math.abs(x)),y=1-(((((1.061405429*t-1.453152027)*t)+1.421413741)*t-0.284496736)*t+0.254829592)*t*Math.exp(-x*x);return x>=0?y:-y};
 const Phi=z=>0.5*(1+erf(z/Math.SQRT2));
 function renderCmp(){const box=$('#x-cmp');if(S.view!=='P'||!S.cmp.length){box.hidden=true;return}
   const L=S.cmp.map(k=>{const [y,i]=k.split('|');return Object.assign({k,y},D.seasons[y].players[+i])});
   const rows=L.map(r=>`<tr><td><b>${esc(r.n)}</b> <span class="muted">${r.y}</span></td><td>${esc(r.t)}</td><td>${esc(r.l)}</td><td>${r.r}</td><td class="r">${r.gp}</td><td class="r">${fmt(U(r.p))}${US()} <span class="muted">± ${fmt(U(r.sd))}</span></td><td class="r"><button type="button" class="x-cmp-btn" data-k="${r.k}" aria-label="Retirer ${esc(r.n)}">×</button></td></tr>`).join('');
   const pr=[];for(let i=0;i<L.length;i++)for(let j=i+1;j<L.length;j++){const a=L[i],b=L[j],z=(a.p-b.p)/Math.hypot(a.sd,b.sd);const w=z>=0?[a,b,Phi(z)]:[b,a,Phi(-z)];pr.push(`${esc(w[0].n)} meilleur que ${esc(w[1].n)} : ${pct(w[2])}`)}
   box.innerHTML=`<div class="x-cmp-head"><b>Comparaison</b> <button type="button" id="x-cmp-clear">Tout retirer</button></div><div class="tbl-wrap"><table class="mini"><thead><tr><th>Joueur</th><th>Équipe</th><th>Ligue</th><th>Poste</th><th class="r">Games</th><th class="r">Note</th><th></th></tr></thead><tbody>${rows}</tbody></table></div>`+
     (pr.length?`<p class="muted" style="margin:6px 0 0">${pr.join(' · ')} <span title="Probabilité que la vraie note de l'un dépasse celle de l'autre, compte tenu des incertitudes (notes de saisons différentes : à prendre avec précaution).">(?)</span></p>`:'<p class="muted" style="margin:6px 0 0">Ajoute un deuxième joueur depuis sa fiche.</p>');
   box.hidden=false;$('#x-cmp-clear').onclick=()=>{S.cmp=[];renderCmp();render()};}
 const render=()=>{(S.view==='P'?renderPlayers:renderTeams)();renderCmp()};
 document.querySelector('.explorer').addEventListener('click',e=>{const bt=e.target.closest('.x-cmp-btn');if(!bt)return;e.stopPropagation();const k=bt.dataset.k;
   S.cmp=S.cmp.includes(k)?S.cmp.filter(x=>x!==k):[...S.cmp,k].slice(-4);render()},true);
 const upd=(k,v)=>{S[k]=v;S.shown=25;S.open=null;if(k==='season')index();fillSelects();render();save()};
 for(const [id,k] of [['#x-season','season'],['#x-view','view'],['#x-tier','tier']])$(id).addEventListener('click',e=>{const b=e.target.closest('button');if(b)upd(k,b.dataset.v)});
 for(const [id,k] of [['#x-region','region'],['#x-league','league'],['#x-comp','comp'],['#x-role','role'],['#x-path','path'],['#x-sort','sort'],['#x-unit','unit']])$(id).addEventListener('change',e=>upd(k,e.target.value));
 $('#x-min').addEventListener('input',e=>{$('#x-min-v').textContent=e.target.value;upd(cmode()?'minc':'min',+e.target.value)});
 $('#x-q').addEventListener('input',e=>{S.q=e.target.value;S.shown=25;render()});
 $('#x-more').addEventListener('click',()=>{S.shown+=25;render()});
 const toggle=tr=>{if(!tr)return;const k=tr.dataset.k;S.open=S.open===k?null:k;render();const again=[...document.querySelectorAll('#x-table tr.prow')].find(x=>x.dataset.k===k);again&&again.focus()};
 $('#x-table').addEventListener('click',e=>{if(S.view==='P')toggle(e.target.closest('tr.prow'))});
 $('#x-table').addEventListener('keydown',e=>{if(S.view==='P'&&(e.key==='Enter'||e.key===' ')){const tr=e.target.closest('tr.prow');if(tr){e.preventDefault();toggle(tr)}}});
 index();fillSelects();render();}
table($('#t-under'),[{h:'Joueur',k:'player'},{h:'Équipe',k:'team'},{h:'Ligue',k:'league26'},{h:'Rôle',k:'role'},{h:'Points LR3',r:1,f:r=>fmt(r.points)},{h:'N°1 hors majeures',r:1,f:r=>pct(r.p1)},{h:'Top 10',r:1,f:r=>pct(r.p10)},{h:'Coéquipiers',r:1,f:r=>r.teammates}],D.underrated,(r,i)=>i==0);
draw();let rt;addEventListener('resize',()=>{clearTimeout(rt);rt=setTimeout(draw,150)});
</script>
'''
CSS=CSS.replace('--div-neg:#C4562B; --div-pos:#1F6FB8; --div-mid:#E6E9EE;','--div-neg:#C4562B; --div-pos:#1F6FB8; --div-mid:#E6E9EE;\n  --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a;',1)
CSS=CSS.replace('--div-neg:#E07A4D; --div-pos:#5A9BE0; --div-mid:#1C2A3D; color-scheme:dark}}','--div-neg:#E07A4D; --div-pos:#5A9BE0; --div-mid:#1C2A3D; --s1:#3987e5; --s2:#d95926; --s3:#199e70; color-scheme:dark}}',1)
CSS=CSS.replace('--div-neg:#E07A4D; --div-pos:#5A9BE0; --div-mid:#1C2A3D; color-scheme:dark}\n','--div-neg:#E07A4D; --div-pos:#5A9BE0; --div-mid:#1C2A3D; --s1:#3987e5; --s2:#d95926; --s3:#199e70; color-scheme:dark}\n',1)
CSS=CSS.replace('h3{font-size:22px;','h3{margin-top:10px;font-size:22px;')
CSS=CSS.replace('</style>','''.explorer{display:flex;flex-direction:column;gap:12px;background:var(--surface);border:1px solid var(--rule);padding:16px}
.controls{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px 14px}
.controls label{display:flex;flex-direction:column;gap:4px;font:500 11px/1.2 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);min-width:0}
.controls .grow{grid-column:span 2}
@media (max-width:560px){.controls .grow{grid-column:auto}}
.controls select,.controls input[type=search]{font:400 14px/1.2 var(--body);letter-spacing:0;text-transform:none;color:var(--ink);background:var(--bg);border:1px solid var(--rule);padding:7px 8px;width:100%;min-width:0}
.controls input[type=range]{width:100%;accent-color:var(--gold)}
.controls select:focus-visible,.controls input:focus-visible,.x-more:focus-visible{outline:2px solid var(--gold);outline-offset:1px}
.x-info{font-size:13.5px;min-height:1.2em}
.xbar{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center}
[hidden]{display:none!important}
tr.prow{cursor:pointer}
tr.prow:hover td{background:var(--gold-soft)}
tr.prow:focus-visible{outline:2px solid var(--gold);outline-offset:-2px}
tr.pdetail td{white-space:normal;background:var(--bg);padding:14px}
.pcard{display:flex;flex-wrap:wrap;gap:14px 24px;align-items:flex-start}
.pcard-main{flex:1 1 320px;min-width:0;display:flex;flex-direction:column;gap:6px;font-size:14px}
.pcard-chart{flex:0 0 330px;max-width:100%;min-width:0}
tr.pdetail td{white-space:normal}
.x-cmp{background:var(--surface);border:1px solid var(--rule);border-left:3px solid var(--gold);padding:10px 12px}
.x-cmp-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.x-cmp button,.x-cmp-btn{font:inherit;font-size:13px;padding:4px 10px;background:transparent;color:var(--ink);border:1px solid var(--rule);cursor:pointer}
.x-cmp-btn:hover,.x-cmp button:hover{border-color:var(--gold)}
.calc{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end;margin:14px 0 6px}
.calc label{display:flex;flex-direction:column;gap:4px;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);flex:1 1 220px}
.calc select{font:inherit;font-size:15px;text-transform:none;letter-spacing:0;padding:8px 10px;background:var(--surface);color:var(--ink);border:1px solid var(--rule)}
.w-out{flex:1 1 100%;font-size:15px;padding:10px 12px;background:var(--surface);border-left:3px solid var(--gold)}
.pcard{position:sticky;left:0;max-width:min(940px,calc(100vw - 96px))}
@media (max-width:600px){table.mini{font-size:12px;width:100%;table-layout:fixed}table.mini td,table.mini th{padding:4px 4px}table.mini th:first-child{width:36%}.hide-sm{display:none}table.mini td:first-child{min-width:0}}
table.mini td:first-child{white-space:normal;min-width:120px}
table.mini td{white-space:nowrap}
.lineup{white-space:normal;font-size:13px}
table.mini{width:auto;font-size:13px;margin-top:4px}
table.mini td,table.mini th{padding:4px 8px}
.x-more{align-self:flex-start;font:600 13px/1 var(--body);padding:9px 14px;border:1px solid var(--rule);background:var(--bg);color:var(--ink);cursor:pointer}
</style>''')
HEAD='''<title>LoL Ratings 3.0</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;800;900&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
'''
data=json.dumps(D,ensure_ascii=False).replace('</','<\\/')
out=HEAD+CSS+BODY+JS.replace('__DATA__',data)
open('page/lol-ratings-3.html','w').write(out)
# version publiée sur GitHub Pages (Settings > Pages > Deploy from a branch > main /docs)
import os; os.makedirs('docs',exist_ok=True)
open('docs/index.html','w').write('<!doctype html>\n<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<style>body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>\n'+out.replace('</style>','</style>\n</head><body>',1)+'\n</body></html>\n')
open('docs/.nojekyll','w').write('')
assert CSS.count('--s1:')==3, CSS.count('--s1:')
print('page ok',len(out))
