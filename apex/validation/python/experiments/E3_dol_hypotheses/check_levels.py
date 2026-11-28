import numpy as np, pandas as pd, common_load as C, e3lib as L
for nm, tf in (("NQ", "1h"), ("BTC", "1h"), ("NQL", "5m")):
    o = C.get(nm, tf); df, lv = o["df"], o["lv"]
    h, l = df.high.values, df.low.values
    bad = 0
    for kind in (L.PD, L.PW, L.SES):
        key = {L.PD: "day", L.PW: "week", L.SES: "sessid"}[kind]
        sub = lv[lv.kind == kind].sample(min(200, (lv.kind == kind).sum()), random_state=1)
        for _, r in sub.iterrows():
            a, b = int(r.origin), int(r.avail)
            k = df[key].values
            assert k[a] == k[b] and (b + 1 >= len(df) or k[b + 1] != k[b]) and (a == 0 or k[a - 1] != k[a]), "instance bounds"
            want = h[a:b + 1].max() if r.side > 0 else l[a:b + 1].min()
            bad += want != r.price
            # expiry = end of next instance
            e = int(r.exp)
            assert e > b and (e >= len(df) or kind == L.SES or k[e] != k[b + 1]), "expiry"
    sw = lv[lv.kind == L.SW]
    assert (sw.avail - sw.origin == 5).all()
    fv = lv[lv.kind == L.FVG]
    assert (fv.avail - fv.origin == 1).all()
    pools = lv[lv.kind != L.FVG]
    assert (pools.end > pools.avail).all()
    # end really is first strict trade-through
    s = pools[pools.traded].sample(300, random_state=2)
    for _, r in s.iterrows():
        a, e = int(r.avail) + 1, int(r.end)
        seg = (h[a:e + 1] > r.price) if r.side > 0 else (l[a:e + 1] < r.price)
        assert seg[-1] and not seg[:-1].any()
    print(nm, tf, "PD/PW/SES price mismatches:", bad, "| asserts ok")
    # htf bias uses only completed htf bars: bias constant within an htf bar
    key = "day" if tf == "1h" else "hourk"
    g = df.groupby(key).htf_bias.nunique()
    print("   htf bias constant within HTF bar:", (g == 1).all(), " share bull/bear/none:",
          np.round([(df.htf_bias > 0).mean(), (df.htf_bias < 0).mean(), (df.htf_bias == 0).mean()], 3))
