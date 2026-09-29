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
V11=R['v1.1 ré-entraînée chaque mois']; ELO=R['Elo équipe (mis à jour à chaque game)']; ELOJ=R['Elo joueurs (mis à jour à chaque game)']
KDAR=R['KDA à date']; FROZ=R['v1.0 (2025 seul, gelée)']; COMB=R['v1.1 + Elo (combinés)']; TAU=R['v1.1 + oubli progressif (1 an)']
months_better=sum(1 for m in M['v1.1 ré-entraînée chaque mois'] if M['v1.1 ré-entraînée chaque mois'][m]['auc']>M['Elo équipe (mis à jour à chaque game)'][m]['auc'])
nmonths=len(M['v1.1 ré-entraînée chaque mois'])
S=D['scouting']; U=D['underrated']; RT=D['ratones']; REL=D['reliab']; MV=D['mv']; TOP=D['top']
t50=D['v03_top50']; t50s=sorted(t50.items(),key=lambda kv:-kv[1])
top50_txt=', '.join(f'{v} de {k}' for k,v in t50s[:3])
pairs=D['pairs']
C=D['counter']; cp={k:C[k]['champ']/2 for k in C}; cpse={k:C[k]['champ_se']/2 for k in C}
TL={t['kind']:t for t in D['tilt']}
t_same=TL['même série (quelques minutes après)']; t_next=TL['prochaine rencontre (<60 j)']
maj=TOP['Ligue majeure']; aca=TOP['Académie / ligue régionale']
no1={ro:maj[ro][0] for ro in maj}
no1_teams=[no1[r]['team'] for r in ['Top','Jungle','Mid','ADC','Support']]
ROLES=['Top','Jungle','Mid','ADC','Support']
mvw={r:MV['roles']['Ligue majeure'][r][0] for r in ROLES}
GENG_GAMES=D.get('geng_games',0)
u0=U[0]
games25=D['games']['2025']; games26=D['games']['2026']
ch=MV['choice_effects']
LC=D['league_check']; mov={x['origine']:x for x in LC['movers']}; LN=D['leagues_now']

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
  <p class="muted" style="font-size:14px">Inspiré de la méthode de la vidéo <a href="https://www.youtube.com/watch?v=0I2T0R91G38">« the most average NBA player »</a> (<a href="https://github.com/HQEye/basic-most-average-nba-player">code</a>) et parti du notebook <i>LoL Ratings 2.0</i>. Données : Oracle's Elixir, jusqu'au 28 septembre 2026.</p>
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
    <figcaption>Points LR3 du joueur moyen de chaque ligue (0 = joueur moyen actif en 2026). 100 points ≈ 500 golds d'écart final par game et par joueur. Modèle entraîné sur toutes les games jusqu'au 28 septembre 2026. Les ligues peu reliées aux autres ont les estimations les plus fragiles.</figcaption>
  </figure>
  <div class="callout"><span class="eyebrow">LCK CL ou LEC&nbsp;?</span><p>Avec la seule saison 2025, le modèle mettait la LCK Challengers au niveau de la LEC ({sgn(LC['diff']['LCKC-LEC'][0])} points, avec une incertitude de ±{n(LC['diff']['LCKC-LEC'][1])}) : trop peu de joueurs relient les deux ligues pour trancher. Les transferts de l'intersaison ont servi de test. Les joueurs partis de la LCK CL vers une autre ligue ont fait {sgn(mov['LCKC']['points_par_joueur'])} points par joueur par rapport à leur note 2025 (±{n(mov['LCKC']['se'])}), ceux partis de la LEC {sgn(mov['LEC']['points_par_joueur'])} (±{n(mov['LEC']['se'])}). La LEC était donc sous-estimée. Une fois 2026 intégrée, la LEC passe nettement devant ({sgn(LN['LEC'])} contre {sgn(LN['LCKC'])}).</p></div>
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
    <figcaption>AUC de chaque mois. La v1.0 gelée (notes 2025 jamais mises à jour) décroche en fin de saison ; la v1.1 ré-entraînée tient.</figcaption>
  </figure>
  <p>La v1.1 fait mieux que l'Elo d'équipe {months_better} mois sur {nmonths}. La combiner avec les deux Elo n'apporte rien (AUC {n(COMB['auc'],3)} contre {n(V11['auc'],3)}) : l'Elo ne sait rien que le modèle ne sache déjà. L'oubli progressif n'aide pas non plus ({n(TAU['auc'],3)}).</p>
  <p>Deux vérifications contre l'auto-persuasion. Un placebo : si je mélange au hasard les résultats de 2025, le modèle retombe à une AUC de {n(D['placebo'],2)} sur janvier 2026. Il ne triche donc pas. Et la stabilité : en coupant 2025 en deux moitiés au hasard, les notes des deux moitiés sont corrélées à {n(REL['v1 theta'],2)}. Le KDA fait {n(REL['KDA'],2)}, mais il est stable parce que la force d'une équipe est stable. Stable ne veut pas dire juste.</p>
</div></section>

<section><div class="col">
  <span class="eyebrow">Les notes 2026 · le multivers</span>
  <h2>Qui est le meilleur à chaque poste&nbsp;?</h2>
  <p>Comme dans la vidéo, je ne choisis pas une version. J'en tire {n(MV['auc']['n'])} au hasard, toutes défendables : force de la régularisation, cible (victoire, or, mélange), poids par rôle ou globaux, correction du champion, stats de lane, chaque stat retirée avec une probabilité de 15&nbsp;%, oubli progressif, minimum de games. Chaque version est notée sur août-septembre 2026 (AUC de {n(MV['auc']['min'],3)} à {n(MV['auc']['max'],3)}), puis ré-entraînée sur tout jusqu'au 28 septembre 2026.</p>
  <p>Les académies et ligues régionales ont leur propre tableau : leurs joueurs n'affrontent presque jamais ceux des ligues majeures, les mélanger dans un même classement serait trompeur.</p>
  <div class="role-tabs" role="group" aria-label="Choisir un rôle" id="tabs"></div>
  <h3>Ligues majeures <span class="muted" style="font-size:14px;font-family:var(--body);text-transform:none;letter-spacing:0">LCK, LPL, LEC, LCS, CBLOL, LCP</span></h3>
  <div class="tbl-wrap bleed"><table id="t-major"></table></div>
  <h3>Académies et ligues régionales</h3>
  <div class="tbl-wrap bleed"><table id="t-acad"></table></div>
  <p class="muted" style="font-size:13.5px">Joueurs à 20 games ou plus en 2026. Points LR3 ± écart-type (incertitude statistique) ; « vs rôle de sa ligue » = golds d'écart final par game par rapport au joueur moyen du même rôle dans sa ligue ; « n°1 multivers » = part des {n(MV['auc']['n'])} versions où il est n°1 de son rôle dans ce tableau ; « n°1 incertitude » = même chose en tirant 4&nbsp;000 fois dans l'incertitude statistique.</p>
  <p class="verdict">Version de référence : {', '.join(E(no1[r]['name'])+' ('+E(no1[r]['team'])+')' for r in ROLES)}. Le multivers, lui, désigne {', '.join(E(mvw[r]['player'])+' ('+pct(mvw[r]['mv_p1'])+')' for r in ROLES)}.</p>
  <p>Chovy et Ruler sont n°1 dans {'toutes les versions' if min(mvw['Mid']['mv_p1'],mvw['ADC']['mv_p1'])>=0.995 else 'presque toutes les versions'}. En top et en jungle, le multivers hésite entre un joueur de Gen.G et un joueur d'une autre équipe. Ce n'est pas un hasard : Gen.G a aligné exactement les mêmes cinq joueurs en 2025 et en 2026 ({n(GENG_GAMES)} games ensemble cette saison). Le problème de 2025 n'a pas disparu : aucune version ne peut dire lequel des cinq porte les autres, et c'est pour ça que les choix de modélisation font basculer le n°1.</p>
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
  <p class="muted">Avec la réserve qui s'impose : {E(u0['player'])} a joué avec {u0['teammates']} coéquipiers différents en deux ans. Plus ce nombre est petit, plus sa note peut appartenir en partie à son équipe. Même angle mort que Gen.G, en plus petit.</p>
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
  <p>Code : Python (pandas, NumPy, SciPy, scikit-learn). Données : <a href="https://oracleselixir.com/tools/downloads">Oracle's Elixir</a>, match data 2022, 2025 et 2026 (jusqu'au 28 septembre). Méthode inspirée de B.A.S.I.C. (HQEye). Notes = ridge « RAPM » sur l'écart d'or, prior « stats » appris par rôle, niveaux de ligue portés par les joueurs.</p>
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
  cats.forEach((c,i)=>{const tx=el('text',{x:x(i),y:H-B+18,'text-anchor':'middle'},ax);tx.textContent=W<480?c.full[0]:c.label});
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
  const R=D.rolling.total;const rn=['KDA à date','v1.0 (2025 seul, gelée)','Elo équipe (mis à jour à chaque game)','Elo joueurs (mis à jour à chaque game)','v1.1 + Elo (combinés)','v1.1 ré-entraînée chaque mois'];
  const rl={'KDA à date':'KDA (mis à jour chaque mois)','v1.0 (2025 seul, gelée)':'v1.0 gelée (notes 2025)','Elo équipe (mis à jour à chaque game)':'Elo équipe (chaque game)','Elo joueurs (mis à jour à chaque game)':'Elo joueurs (chaque game)','v1.1 + Elo (combinés)':'v1.1 + Elo combinés','v1.1 ré-entraînée chaque mois':'v1.1 (chaque mois)'};
  hbar($('#f-rolling'),rn.map(k=>({label:rl[k],value:R[k].auc,lo:R[k].auc_lo,hi:R[k].auc_hi,acc:R[k].acc,hl:k==='v1.1 ré-entraînée chaque mois',tip:`<b>${esc(rl[k])}</b><br>AUC ${fmt(R[k].auc,3)} [${fmt(R[k].auc_lo,3)} – ${fmt(R[k].auc_hi,3)}]<br>${pct(R[k].acc,1)} de bonnes prédictions`})),
    {left:200,right:100,row:28,base:.5,min:.5,max:.76,ticks:[.5,.55,.6,.65,.7,.75],tf:t=>fmt(t,2),vf:d=>`${fmt(d.value,3)} (${pct(d.acc,1)})`,aria:'AUC saison 2026'});
  const M=D.rolling.monthly,MN=['févr.','mars','avr.','mai','juin','juil.','août','sept.'],FULL=['Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre'];
  const keys=Object.keys(M['v1.1 ré-entraînée chaque mois']);const cats=keys.map((k,i)=>({label:MN[i],full:FULL[i]+' 2026'}));
  const ser=[['v1.1','v1.1 ré-entraînée chaque mois','var(--s1)',0],['Elo équipe','Elo équipe (mis à jour à chaque game)','var(--s2)',0],['v1.0 gelée','v1.0 (2025 seul, gelée)','var(--s3)',0]]
    .map(([name,k,color])=>({name,color,v:keys.map(m=>M[k][m].auc)}));
  const ends=ser.map(s=>s.v[s.v.length-1]);ser.forEach((s,i)=>{for(let j=0;j<i;j++)if(Math.abs(ends[i]-ends[j])<.012)s.dy=(s.dy||0)+(ends[i]<ends[j]?12:-12)});
  const all=ser.flatMap(s=>s.v);lines($('#f-monthly'),ser,cats,{min:Math.floor(Math.min(...all)*50)/50-.01,max:Math.ceil(Math.max(...all)*50)/50,ticks:[.6,.65,.7,.75].filter(t=>t>=Math.min(...all)-.02&&t<=Math.max(...all)+.02),aria:'AUC par mois'});
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
{const roles=['Top','Jungle','Mid','ADC','Support'];let cur='Mid';
 const cols=[{h:'#',r:1,f:(r,i)=>i+1},{h:'Joueur',k:'name'},{h:'Équipe',k:'team'},{h:'Ligue',k:'league'},{h:'Points LR3',r:1,f:r=>`${fmt(r.pts)} <span class="muted">± ${fmt(r.sd)}</span>`},{h:'vs rôle de sa ligue',r:1,f:r=>(r.u_gold>0?'+':'')+fmt(r.u_gold)+' g'},{h:'N°1 multivers',r:1,f:r=>pct(r.mv_p1)},{h:'N°1 incertitude',r:1,f:r=>pct(r.post_p1)}];
 function render(){table($('#t-major'),cols,D.top['Ligue majeure'][cur],(r,i)=>i==0);table($('#t-acad'),cols,D.top['Académie / ligue régionale'][cur],(r,i)=>i==0);
  document.querySelectorAll('#tabs button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.r===cur))}
 $('#tabs').innerHTML=roles.map(r=>`<button type="button" id="tab-${r}" data-r="${r}">${r}</button>`).join('');
 $('#tabs').addEventListener('click',e=>{const b=e.target.closest('button');if(b){cur=b.dataset.r;render()}});render();}
table($('#t-under'),[{h:'Joueur',k:'player'},{h:'Équipe',k:'team'},{h:'Ligue',k:'league26'},{h:'Rôle',k:'role'},{h:'Points LR3',r:1,f:r=>fmt(r.points)},{h:'N°1 hors majeures',r:1,f:r=>pct(r.p1)},{h:'Top 10',r:1,f:r=>pct(r.p10)},{h:'Coéquipiers',r:1,f:r=>r.teammates}],D.underrated,(r,i)=>i==0);
draw();let rt;addEventListener('resize',()=>{clearTimeout(rt);rt=setTimeout(draw,150)});
</script>
'''
CSS=CSS.replace('--div-neg:#C4562B; --div-pos:#1F6FB8; --div-mid:#E6E9EE;','--div-neg:#C4562B; --div-pos:#1F6FB8; --div-mid:#E6E9EE;\n  --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a;',1)
CSS=CSS.replace('--div-neg:#E07A4D; --div-pos:#5A9BE0; --div-mid:#1C2A3D; color-scheme:dark}}','--div-neg:#E07A4D; --div-pos:#5A9BE0; --div-mid:#1C2A3D; --s1:#3987e5; --s2:#d95926; --s3:#199e70; color-scheme:dark}}',1)
CSS=CSS.replace('--div-neg:#E07A4D; --div-pos:#5A9BE0; --div-mid:#1C2A3D; color-scheme:dark}\n','--div-neg:#E07A4D; --div-pos:#5A9BE0; --div-mid:#1C2A3D; --s1:#3987e5; --s2:#d95926; --s3:#199e70; color-scheme:dark}\n',1)
CSS=CSS.replace('h3{font-size:22px;','h3{margin-top:10px;font-size:22px;')
HEAD='''<title>LoL Ratings 3.0</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;800;900&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
'''
data=json.dumps(D,ensure_ascii=False).replace('</','<\\/')
out=HEAD+CSS+BODY+JS.replace('__DATA__',data)
open('page/lol-ratings-3.html','w').write(out)
assert CSS.count('--s1:')==3, CSS.count('--s1:')
print('page ok',len(out))
