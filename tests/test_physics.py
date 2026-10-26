from pathlib import Path
from playwright.sync_api import sync_playwright
from scipy.integrate import solve_ivp
import math,shutil
ROOT=Path(__file__).resolve().parents[1]
def reference(v,rotating=True):
 A,B,C,D,E,kind=v;mass,radius,cd=(.0027,.02,.47) if kind==0 else (.04593,.021335,.25);a,b=map(math.radians,[A,B]);delta=math.radians(B-100) if rotating else 0;r=C/1000;q=E/1000;p=D/1000*1.22;fy=-15/620;ax=.20*math.cos(delta)-fy*math.sin(delta)-p*math.sin(delta);ay=.20*math.sin(delta)+fy*math.cos(delta)+p*math.cos(delta)
 I=.025*.46**2/3+(.006+mass)*r*r;gm=9.80665*(.025*.23+(.006+mass)*r)
 def arm(t,z):
  theta,w=z;L=math.hypot(q*math.cos(theta)-ax,q*math.sin(theta)-ay);extension=max(0,L+abs(ay-fy)-.35);torque=36*extension*q*(ax*math.sin(theta)-ay*math.cos(theta))/L+gm*math.cos(theta)-.0003-.00008*w;return [-w,torque/I]
 def release(t,z):return z[0]-b
 release.direction=-1;release.terminal=True
 armSol=solve_ivp(arm,[0,3],[a,0],events=release,max_step=.001,atol=1e-12,rtol=1e-11);assert armSol.t_events[0].size
 w=armSol.y_events[0][0][1];speed=r*w;angle=b-math.pi/2;h=33/620+r*math.sin(b);drag=.5*1.225*cd*math.pi*radius**2/mass
 def ball(t,z):
  x,y,vx,vy=z;v=math.hypot(vx,vy);return [vx,vy,-drag*v*vx,-9.80665-drag*v*vy]
 def landing(t,z):return z[1]
 landing.direction=-1;landing.terminal=True
 sol=solve_ivp(ball,[0,10],[0,h,speed*math.cos(angle),speed*math.sin(angle)],events=landing,max_step=.002,atol=1e-12,rtol=1e-11)
 return sol.y_events[0][0][0]*100

with sync_playwright() as p:
 b=p.chromium.launch(**({'executable_path':shutil.which('chromium')} if shutil.which('chromium') else {}),args=['--no-sandbox'])
 for filename,rotating in [('DOE_Catapult_Competition.html',False),('DOE_Catapult_Reference_Layout.html',False)]:
  page=b.new_page();page.set_content((ROOT/filename).read_text())
  for settings in [[145,110,300,200,200,k] for k in [0,1]]+[[180,120,420,200,200,k] for k in [0,1]]+[[120,100,420,200,200,k] for k in [0,1]]:
   result=page.evaluate('v=>model(v)',settings);assert result['valid']
   expected=reference(settings,rotating)
   assert abs(result['distance']-expected)<.08,(settings,result['distance'],expected)
   assert abs(result['energy']['residual'])<.0004
  print(filename+': independent SciPy integration and energy balance PASS')
  page.close()
 b.close()
