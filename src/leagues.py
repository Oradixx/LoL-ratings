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
def tier(home_league):
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
 'LCP':'Asie-Pacifique','PCS':'Asie-Pacifique','VCS':'Asie-Pacifique','LJL':'Asie-Pacifique'}
DESC={
 'LCK':'Corée','LCKC':'LCK Challengers (académies LCK)','LAS':'LCK Academy Series (2e équipe des académies LCK)','LPL':'Chine',
 'LEC':'Europe','LFL':'France','NL':'France, Nexus League (2e division)','LFL2':'France, 2e division','PRM':'Allemagne (Prime League)',
 'LES':'Espagne','TCL':'Turquie','NLC':'Royaume-Uni & pays nordiques','LIT':'Italie','HLL':'Grèce & Chypre','EBL':'Balkans',
 'RL':'Pologne & Europe centrale','ROL':'Benelux','HM':'Tchéquie & Slovaquie','HC':'Tchéquie & Slovaquie, 2e division',
 'LPLOL':'Portugal','AL':'Moyen-Orient & Afrique du Nord',
 'LCS':'Amérique du Nord','NACL':'Amérique du Nord, 2e niveau','CBLOL':'Brésil (+ équipes LATAM en 2025)','CD':'Brésil, 2e niveau',
 'LRN':'Amérique latine Nord','LRS':'Amérique latine Sud',
 'LCP':'Pacifique (Taïwan, Vietnam, Japon…)','PCS':'Taïwan, Hong Kong & Asie du Sud-Est','VCS':'Vietnam','LJL':'Japon'}
