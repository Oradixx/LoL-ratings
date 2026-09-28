import sys; sys.path.insert(0,'src'); from engine import *
import time
p=player_games((2025,)); g=game_table(p)
t=time.time(); m=fit(p,g,dict(lam=30,lamL=30,target='result')); print('fit s',round(time.time()-t,1))
r=rating_table(m,p)
print('league effects:'); print(m['league'].sort_values(ascending=False).round(3).to_string())
print('prior weights:'); print(m['prior_w'].round(4).sort_values().to_string())
for role in ['Top','Jungle','Mid','ADC','Support']:
    print(role, r[(r.role==role)&(r.gp>=15)].sort_values('theta',ascending=False).head(8)[['name','team','home','gp','u','theta']].round(3).values.tolist())
