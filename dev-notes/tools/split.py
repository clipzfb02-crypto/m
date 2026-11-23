# split a Pine file into top-level statements (one chunk each), as standalone parseable files
import sys, os
src = open(sys.argv[1], encoding="utf-8").read().splitlines()
out = sys.argv[2]
os.makedirs(out, exist_ok=True)
chunks, cur, start = [], [], 0
for i, line in enumerate(src):
    if i == 0:
        continue
    top = line and not line[0].isspace() and not line.startswith("//")
    if top and cur:
        chunks.append((start, cur)); cur = []
    if top and not cur:
        start = i + 1
    if cur or top:
        cur.append(line)
if cur: chunks.append((start, cur))
for n, (ln, lines) in enumerate(chunks):
    open(os.path.join(out, f"c{n:03d}_L{ln}.pine"), "w", encoding="utf-8").write("//@version=5\n" + "\n".join(lines) + "\n")
print(len(chunks))
