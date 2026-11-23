import sys
from pynescript.ast import parse
src = open(sys.argv[1], encoding="utf-8").read()
try:
    parse(src)
    print("parsed OK")
except Exception as e:
    print("PARSE ERROR:", type(e).__name__, str(e)[:500])
    sys.exit(1)
