"""Noms de ligues harmonisés entre les années.

2025 : Riot a fusionné l'Amérique en LTA, avec deux conférences.
  - LTA N (Nord)  = mêmes équipes que la LCS  -> 'LCS'
  - LTA S (Sud)   = CBLOL + équipes LATAM     -> 'CBLOL'
  - LTA (sans N/S) = LTA Championship, matchs croisés Nord/Sud -> traité comme un tournoi international
2026 : retour de la LCS et du CBLOL. La SuperLiga espagnole (LVP SL) devient la LES.
"""
CANON={'LTA N':'LCS','LTA S':'CBLOL',
       'LFL2':'NL',             # LFL Division 2 (2025) devenue la Nexus League (2026)
       'LVP SL':'LES',          # SuperLiga (Espagne) renommée LES en 2026
       'Asia Master':'AM'}      # nom du miroir GitHub vs fichier officiel
INTL={'MSI','EWC','FST','WLDs','Asia Master','EM','LTA'}      # tournois qui relient plusieurs ligues
MAJOR={'LCK','LPL','LEC','LCS','CBLOL','LCP'}                 # ligues majeures (structure 2025-2026)
LABEL={'LCS':'LCS (LTA Nord en 2025)','CBLOL':'CBLOL (LTA Sud en 2025)'}
def canon(league):
    return CANON.get(league,league)
TIER3={'LAS','NL','HC','NEXO'}                       # 3e niveau : académies LCK (2e équipe), Nexus League, Hitpoint Challengers, Liga Nexo
TIERS=['Ligue majeure','Deuxième niveau','Troisième niveau']
# 2023-2024 : avant la fusion en LTA (Amériques) et en LCP (Pacifique), les ligues de premier niveau (qualificatives
# pour les Worlds) étaient plus nombreuses : PCS, VCS, LJL, LLA et LCO en plus des quatre grandes et du CBLOL.
MAJOR_2324={'LCK','LPL','LEC','LCS','CBLOL','PCS','VCS','LJL','LLA','LCO'}
TIER3_2324={'LAS','NL','HC','NEXO','NLC Aurora Open','IGNIS'}
def majors(year=None):
    return MAJOR_2324 if year in (2023,2024) else MAJOR
# ligue qui prend la suite d'une autre (pour l'a priori « niveau de la saison d'avant ») : vérifié sur les équipes
# et les joueurs communs (Ultraliga -> Rift Legends, Elite Series -> Road of Legends, GLL -> HLL,
# CBLOL Academy -> Circuito Desafiante, LLA -> LRN)
SUCCESSOR_OF={'RL':'UL','ROL':'ESLOL','HLL':'GLL','CD':'CBLOLA','LRN':'LLA'}
def tier(home_league,year=None):
    if year in (2023,2024):
        if home_league in MAJOR_2324: return 'Ligue majeure'
        if home_league in TIER3_2324: return 'Troisième niveau'
        if home_league in (None,'INTL_ONLY'): return 'Inconnu'
        return 'Deuxième niveau'
    if home_league in MAJOR: return 'Ligue majeure'
    if home_league in TIER3: return 'Troisième niveau'
    if home_league in (None,'INTL_ONLY'): return 'Inconnu'
    return 'Deuxième niveau'

def detect_cups(p, min_teams=3, share=0.5):
    """Tournois « coupe » détectés dans les données : ligues où au moins la moitié des équipes
    jouent surtout ailleurs (Worlds, MSI, EMEA Masters, Asia Masters, KeSPA Cup, Demacia Cup...).
    Robuste aux codes qui changent d'une année ou d'une version du fichier à l'autre."""
    q=p.assign(team=p.teamid.fillna(p.teamname))
    g=q.groupby(['team','league']).gameid.nunique().reset_index()
    home=g.sort_values('gameid').groupby('team').league.last()
    q=q.drop_duplicates(['team','league'])
    q['foreign']=q.team.map(home)!=q.league
    s=q.groupby('league').agg(n=('team','size'),f=('foreign','mean'))
    return set(s[(s.n>=min_teams)&(s.f>=share)].index)

# Région et description courte de chaque ligue domestique (vérifiées sur les noms d'équipes des fichiers 2025-2026)
REGION={
 'LCK':'Corée','LCKC':'Corée','LAS':'Corée',
 'LPL':'Chine',
 'LEC':'EMEA','LFL':'EMEA','NL':'EMEA','LFL2':'EMEA','PRM':'EMEA','PRMP':'EMEA','LES':'EMEA','NEXO':'EMEA','CT':'EMEA',
 'TCL':'EMEA','NLC':'EMEA','LIT':'EMEA','HLL':'EMEA','EBL':'EMEA','RL':'EMEA','ROL':'EMEA','HM':'EMEA','HC':'EMEA',
 'LPLOL':'EMEA','AL':'EMEA',
 'LCS':'Amérique du Nord','NACL':'Amérique du Nord',
 'CBLOL':'Brésil & Amérique latine','CD':'Brésil & Amérique latine','LRN':'Brésil & Amérique latine','LRS':'Brésil & Amérique latine',
 'LCP':'Asie-Pacifique','PCS':'Asie-Pacifique','VCS':'Asie-Pacifique','LJL':'Asie-Pacifique',
 # 2023-2024
 'LDL':'Chine','UL':'EMEA','ESLOL':'EMEA','PGN':'EMEA','GLL':'EMEA','TSC':'EMEA','NLC Aurora Open':'EMEA',
 'LLA':'Brésil & Amérique latine','CBLOLA':'Brésil & Amérique latine','IGNIS':'Brésil & Amérique latine','LHE':'Brésil & Amérique latine',
 'SL (LATAM)':'Brésil & Amérique latine','GL':'Brésil & Amérique latine','VL':'Brésil & Amérique latine','DDH':'Brésil & Amérique latine',
 'EL':'Brésil & Amérique latine','LMF':'Brésil & Amérique latine',
 'LCO':'Asie-Pacifique','PCL':'Asie-Pacifique','LJLA':'Asie-Pacifique'}
DESC={
 'LCK':'Corée','LCKC':'LCK Challengers (académies LCK)','LAS':'LCK Academy Series (2e équipe des académies LCK)','LPL':'Chine',
 'LEC':'Europe','LFL':'France','NL':'France, Nexus League (2e division)','LFL2':'France, 2e division','PRM':'Allemagne (Prime League)',
 'LES':'Espagne','TCL':'Turquie','NLC':'Royaume-Uni & pays nordiques','LIT':'Italie','HLL':'Grèce & Chypre','EBL':'Balkans',
 'RL':'Pologne & Europe centrale','ROL':'Benelux','HM':'Tchéquie & Slovaquie','HC':'Tchéquie & Slovaquie, 2e division',
 'LPLOL':'Portugal','AL':'Moyen-Orient & Afrique du Nord',
 'LCS':'Amérique du Nord','NACL':'Amérique du Nord, 2e niveau','CBLOL':'Brésil (+ équipes LATAM en 2025)','CD':'Brésil, 2e niveau',
 'LRN':'Amérique latine Nord','LRS':'Amérique latine Sud',
 'LCP':'Pacifique (Taïwan, Vietnam, Japon…)','PCS':'Taïwan, Hong Kong & Asie du Sud-Est','VCS':'Vietnam','LJL':'Japon',
 # 2023-2024
 'LDL':'Chine, 2e division (LDL)','UL':'Pologne (Ultraliga)','ESLOL':'Benelux (Elite Series)','PGN':'Italie (PG Nationals)',
 'GLL':'Grèce & Chypre (GLL)','TSC':'Turquie (TSC)','NLC Aurora Open':'Royaume-Uni & pays nordiques, open',
 'LLA':'Amérique latine (LLA)','CBLOLA':'Brésil, académies (CBLOL Academy)','IGNIS':'Brésil, IGNIS','LHE':'Chili (LHE)',
 'SL (LATAM)':'Amérique latine (Stars League)','GL':'Amérique centrale (Golden League)','VL':'Andes (Volcano League)',
 'DDH':'Amérique du Sud (DDH)','EL':'Amérique centrale (Elements League)','LMF':'Argentine (LMF)',
 'LCO':'Océanie (LCO)','PCL':'Pacifique, 2e division (PCL)','LJLA':'Japon, académies'}

# noms lisibles des compétitions (codes Oracle's Elixir peu parlants)
COMP_EXTRA={'AC':'AC (tournoi LCS–CBLOL, mars)','ASI':'ASI (invitation LCK–LPL–VCS, octobre)','WSCI':'WSCI (invitation des équipes académie, septembre)'}
def comp_labels(comps,home_leagues):
    """comps: {code: {label, league, region, ...}} (sortie de seasons.competitions). Modifie les libellés en place :
    noms lisibles, et « phase de groupes » pour un tournoi qui a aussi des playoffs."""
    for c,meta in comps.items():
        lg=meta['league']
        if lg in COMP_EXTRA: meta['label']=COMP_EXTRA[lg]+meta['label'][len(lg):]
        meta['cup']=lg not in home_leagues
        if meta['cup'] and c==lg and (c+' · playoffs') in comps: meta['label']+=' · phase de groupes'
    return comps
