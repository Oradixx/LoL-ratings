"""Noms de ligues harmonisés entre les années.

2025 : Riot a fusionné l'Amérique en LTA, avec deux conférences.
  - LTA N (Nord)  = mêmes équipes que la LCS  -> 'LCS'
  - LTA S (Sud)   = CBLOL + équipes LATAM     -> 'CBLOL'
  - LTA (sans N/S) = LTA Championship, matchs croisés Nord/Sud -> traité comme un tournoi international
2026 : retour de la LCS et du CBLOL. La SuperLiga espagnole (LVP SL) devient la LES.
"""
CANON={'LTA N':'LCS','LTA S':'CBLOL',
       'LVP SL':'LES',          # SuperLiga (Espagne) renommée LES en 2026
       'Asia Master':'AM'}      # nom du miroir GitHub vs fichier officiel
INTL={'MSI','EWC','FST','WLDs','Asia Master','EM','LTA'}      # tournois qui relient plusieurs ligues
MAJOR={'LCK','LPL','LEC','LCS','CBLOL','LCP'}                 # ligues majeures (structure 2025-2026)
LABEL={'LCS':'LCS (LTA Nord en 2025)','CBLOL':'CBLOL (LTA Sud en 2025)'}
def canon(league):
    return CANON.get(league,league)
def tier(home_league):
    if home_league in MAJOR: return 'Ligue majeure'
    if home_league in (None,'INTL_ONLY'): return 'Inconnu'
    return 'Académie / ligue régionale'

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
