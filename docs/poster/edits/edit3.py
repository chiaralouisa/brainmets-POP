import re
exec(open('edit_poster.py').read().split('# ---- text')[0])
def shift(x,sid,dy):
    a,b=span(x,sid); sp=x[a:b]; (ox,oy,ocx,ocy),m=geom(sp)
    sp=sp[:m.start()]+'<a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"'%(ox,oy+int(dy*E),ocx,ocy)+sp[m.end():]; return x[:a]+sp+x[b:]
# locate rule lines by position: horizontal connectors near (0.6in, 9.6in) and (28.1in, 17.1in)
rules=[]
for m in re.finditer(r'<p:cxnSp>.*?</p:cxnSp>', x, re.S):
    sid=re.search(r'<p:cNvPr id="(\d+)"',m.group(0)).group(1); (ox,oy,ocx,ocy),_=geom(m.group(0))
    ox,oy,ocx=ox/E,oy/E,ocx/E
    if ocx>5 and abs(ox-0.62)<0.2 and abs(oy-9.6)<0.3: rules.append((sid,0.55))
    if ocx>5 and abs(ox-28.17)<0.2 and abs(oy-17.1)<0.3: rules.append((sid,0.3))
print('rules',rules)
for sid,dy in rules: x=shift(x,sid,dy)
a,b=span(x,'229'); sp=x[a:b]
sp=sp.replace('Not CE-IVD or FDA cleared; would be an in-house IVDR device with no monitoring plan.','Not CE-IVD or FDA cleared; an in-house IVDR device without a monitoring plan.')
x=x[:a]+sp+x[b:]
open(P,'w',encoding='utf8').write(x); print('ok')
