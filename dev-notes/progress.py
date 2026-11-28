#!/usr/bin/env python3
"""Overall project progress from workflow journals -> prints a bar and writes dev-notes/PROGRESS.md."""
import json, os, datetime
S='/root/.claude/projects/-home-user-m/7ce60006-3639-59b1-8cd3-87355409d58a/subagents/workflows'
def done(run):
    p=f'{S}/{run}/journal.jsonl'
    if not os.path.exists(p): return 0
    st={};res=set()
    for line in open(p):
        try: j=json.loads(line)
        except: continue
        if j.get('type')=='started': st[j['key']]=j['label']
        if j.get('type')=='result': res.add(j['key'])
    return len({st[k] for k in res if k in st})
# (name, run id or None, done override, total estimate)
extra=json.load(open(os.path.join(os.path.dirname(__file__),'progress_stages.json')))
rows=[];D=T=0
for st in extra:
    auto=sum(done(r) for r in st.get('runs',[]))+(done(st['run']) if st.get('run') else 0)
    d=min(st['total'], st.get('done', auto))
    rows.append((st['name'],d,st['total'])); D+=d; T+=st['total']
def bar(d,t,w=30):
    f=int(round(w*d/t)) if t else 0
    return '█'*f+'░'*(w-f)
pct=100*D/T
out=[f'OVERALL  [{bar(D,T)}] {pct:5.1f}%']
for n,d,t in rows: out.append(f'{n:<31}[{bar(d,t,20)}] {d}/{t}')
txt='\n'.join(out); print(txt)
open(os.path.join(os.path.dirname(__file__),'PROGRESS.md'),'w').write(f'# Progress ({datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M} UTC)\n\n```\n{txt}\n```\n')
