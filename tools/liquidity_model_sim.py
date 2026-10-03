"""
Reference model of Liquidity Flow Pro [Non-Repaint] (liquidity-flow-pro.pine).

A line-for-line Python port of the indicator's confirmed-bar engine, scoring and
flow events. It exists to test the MODEL's behaviour on controlled price paths
(the scenarios from the build spec) and on long random walks, which cannot be
done inside TradingView. Higher-timeframe swings and calendar/intraday session
levels need multi-timeframe data and are not simulated; every other part of the
pipeline is.

Run:  python3 tools/liquidity_model_sim.py
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

SRC_SWING, SRC_HTF, SRC_SES, SRC_PD, SRC_PW, SRC_PM = 0, 1, 2, 3, 4, 5

DEFAULTS = dict(
    swingLen=5, eqTolATR=0.15, maxPools=30, minPoolStr=1.0, maxDistATR=50.0, memoryBars=200, atrLen=14,
    useExt=True, extMult=3, autoScale=True,
    distWeight=1.0, eqWeight=1.5, volWeight=1.0, structWeight=1.0, htfWeight=1.0, sessWeight=1.0,
    smoothLen=3, stability=0.5, balanceThr=8.0,
    flowMode="Liquidity + Structure", pressWeight=1.0, pressLen=10, usePD=False, rangeLen=100, pdWeight=0.5,
    enableSweeps=True, sweepMode="Balanced", keepSwept=True, removeSwept=True, maxSweeps=20,
    extremeLvl=85.0, shiftThr=10.0, shiftLook=5,
    enableSig=False, sigThr=55.0, reqSweep=True, reqStruct=True, sigWindow=10,
)


@dataclass(eq=False)
class Pool:
    id: int
    price: float
    hi: float
    lo: float
    b: int
    isBuy: bool
    src: int
    members: int = 1
    tests: int = 0
    lastTest: int | None = None
    fresh: int = 0
    relVol: float = 1.0
    htf: bool = False
    ext: bool = False
    structural: bool = False
    announced: bool = False
    alive: bool = True
    sweptB: int | None = None
    w: float = 0.0
    dAtr: float = 0.0


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


class Rma:
    """Pine ta.rma: SMA seed over the first `n` values, then Wilder smoothing."""

    def __init__(self, n):
        self.n, self.buf, self.v = n, [], None

    def update(self, x):
        if self.v is None:
            self.buf.append(x)
            if len(self.buf) == self.n:
                self.v = sum(self.buf) / self.n
            return self.v
        self.v = (self.v * (self.n - 1) + x) / self.n
        return self.v


class Ema:
    """Pine ta.ema: SMA seed over the first `n` values, then alpha = 2/(n+1)."""

    def __init__(self, n):
        self.n, self.buf, self.v = n, [], None

    def update(self, x):
        if self.v is None:
            self.buf.append(x)
            if len(self.buf) == self.n:
                self.v = sum(self.buf) / self.n
            return self.v
        a = 2.0 / (self.n + 1)
        self.v = a * x + (1 - a) * self.v
        return self.v


def pivot(series, i, L, high=True):
    """ta.pivothigh/low(L, L) evaluated at bar i -> value of bar i-L or None."""
    c = i - L
    if c - L < 0:
        return None
    v = series[c]
    for j in range(c - L, i + 1):
        if j == c:
            continue
        o = series[j]
        if high and (o > v or (j > c and o == v)):
            return None
        if not high and (o < v or (j > c and o == v)):
            return None
    return v


class Model:
    def __init__(self, bars, **kw):
        self.p = dict(DEFAULTS, **kw)
        self.o, self.h, self.l, self.c, self.v = (list(x) for x in zip(*bars))
        self.n = len(self.c)

    # ── helpers mirroring the Pine functions ───────────────────────────────
    def components(self, p: Pool):
        P = self.p
        sessB = {SRC_SES: 0.20, SRC_PD: 0.25, SRC_PW: 0.50, SRC_PM: 0.75}.get(p.src, 0.0)
        base = 1.0 + P["sessWeight"] * sessB
        cluster = 1.0 + P["eqWeight"] / 1.2 * min(p.members - 1, 3)
        testB = min(p.tests * 0.3, 1.5)
        volB = P["volWeight"] * clamp((min(p.relVol, 3.0) - 1.0) / 2.0, 0.0, 1.0) if self.volOK else 0.0
        structB = (P["structWeight"] if p.structural else 0.0) + (0.5 * P["structWeight"] if p.ext else 0.0)
        htfB = P["htfWeight"] if p.htf else 0.0
        return base, cluster, testB, volB, structB, htfB

    def intrinsic(self, p):
        base, cluster, testB, volB, structB, htfB = self.components(p)
        return base * cluster + testB + volB + structB + htfB

    @staticmethod
    def tier(s):
        return 3 if s >= 4.0 else 2 if s >= 2.75 else 1 if s >= 1.75 else 0

    def time_factor(self, age):
        return 0.5 + 0.5 * math.exp(-max(age, 0) / float(self.memEff))

    def dist_w(self, d):
        return 1.0 / (1.0 + 0.25 * self.p["distWeight"] * d)

    def add_level(self, i, price, originB, isBuy, src, relVol, tol):
        best, bestD = -1, 1e100
        for k, q in enumerate(self.pools):
            if q.isBuy == isBuy:
                d = price - q.hi if price > q.hi else (q.lo - price if price < q.lo else 0.0)
                span = max(q.hi, price) - min(q.lo, price)
                if d <= tol and span <= 2.0 * tol and d < bestD:
                    bestD, best = d, k
        if best >= 0:
            p = self.pools[best]
            same = abs(price - p.hi) <= 1e-9 or abs(price - p.lo) <= 1e-9
            if src == SRC_SWING or not same:
                p.members += 1
                if p.tests > 0 and p.lastTest is not None and p.lastTest == originB:
                    p.tests -= 1
            p.hi, p.lo = max(p.hi, price), min(p.lo, price)
            p.price = p.hi if isBuy else p.lo
            p.relVol = max(p.relVol, relVol)
            p.fresh = i
            if src == SRC_HTF:
                p.htf = True
            if src >= SRC_SES and src > p.src:
                p.src = src
        else:
            self.idseq += 1
            p = Pool(self.idseq, price, price, price, originB, isBuy, src, relVol=relVol, fresh=i, htf=src == SRC_HTF)
            self.pools.append(p)
        return p

    def announce(self, p):
        if p is None:
            return False
        s = self.intrinsic(p)
        if p.alive and not p.announced and self.tier(s) >= 2 and s >= self.p["minPoolStr"]:
            p.announced = True
            return True
        return False

    def enforce_cap(self, i):
        while len(self.pools) > self.p["maxPools"]:
            worst, worstS = 0, 1e100
            for k, q in enumerate(self.pools):
                s = self.intrinsic(q) * self.time_factor(i - q.fresh) * self.dist_w(abs(q.price - self.c[i]) / self.atr)
                if s < worstS:
                    worstS, worst = s, k
            self.pools.pop(worst).alive = False

    # ── main loop ───────────────────────────────────────────────────────────
    def run(self):
        P = self.p
        L = P["swingLen"]
        scale = L / 5.0 if P["autoScale"] else 1.0
        self.memEff = max(20, round(P["memoryBars"] * scale))
        rangeEff = max(20, round(P["rangeLen"] * scale))
        extLen = min(L * P["extMult"], 60)
        self.pools, self.swept, self.idseq = [], [], 0
        recHi, recLo = {}, {}
        atr_rma, tr_prev = Rma(P["atrLen"]), None
        emaB, emaS = Ema(P["smoothLen"]), Ema(P["smoothLen"])
        pressEma = Ema(P["pressLen"])
        dmi_tr, dmi_p, dmi_m = Rma(14), Rma(14), Rma(14)
        lastSH = lastSL = None
        shBroken = slBroken = True
        structDir = 0
        lastBullShiftB = lastBearShiftB = None
        lastSHPool = lastSLPool = None
        domState, lastDirSide, lastShiftB = 0, 0, None
        lastSSLSweepB = lastBSLSweepB = None
        lastBuySigAnchor = lastSellSigAnchor = None
        buyBaseAtSSL = sellBaseAtBSL = None
        out = []
        vols, rv_hist, buyPctHist = [], [], []
        for i in range(self.n):
            o, h, l, c, v = self.o[i], self.h[i], self.l[i], self.c[i], self.v[i]
            tr = h - l if i == 0 else max(h - l, abs(h - self.c[i - 1]), abs(l - self.c[i - 1]))
            a = atr_rma.update(tr)
            self.atr = max(a if a is not None else h - l, 1e-6)
            vols.append(v)
            volAvg = sum(vols[-20:]) / 20 if len(vols) >= 20 else 0.0
            volShare = sum(1 for x in vols[-50:] if x > 0) / 50.0 if len(vols) >= 50 else 0.0
            self.volOK = volShare >= 0.8 and volAvg > 0
            rv_hist.append(v / volAvg if volAvg > 0 else 1.0)
            rvp = 1.0
            if self.volOK and i >= L + 1:
                rvp = (rv_hist[i - L + 1] + rv_hist[i - L] + rv_hist[i - L - 1]) / 3.0
            tol = P["eqTolATR"] * self.atr
            lo_i = max(0, i - rangeEff + 1)
            rangeHi, rangeLo = max(self.h[lo_i:i + 1]), min(self.l[lo_i:i + 1])
            ph, pl = pivot(self.h, i, L, True), pivot(self.l, i, L, False)
            phE = pivot(self.h, i, extLen, True) if P["useExt"] else None
            plE = pivot(self.l, i, extLen, False) if P["useExt"] else None
            ev = dict(i=i, bslSweep=False, sslSweep=False, major=False, taken=0, bos=0)

            # 1) swings
            if ph is not None:
                p = self.add_level(i, ph, i - L, True, SRC_SWING, rvp, tol)
                if ph >= rangeHi:
                    p.structural = True
                recHi[i - L] = p
                lastSH, shBroken, lastSHPool = ph, False, p
                ev["major"] |= self.announce(p)
            if pl is not None:
                p = self.add_level(i, pl, i - L, False, SRC_SWING, rvp, tol)
                if pl <= rangeLo:
                    p.structural = True
                recLo[i - L] = p
                lastSL, slBroken, lastSLPool = pl, False, p
                ev["major"] |= self.announce(p)
            for val, rec, isBuy in ((phE, recHi, True), (plE, recLo, False)):
                if val is not None:
                    p = rec.get(i - extLen)
                    if p is None or not p.alive:
                        p = self.add_level(i, val, i - extLen, isBuy, SRC_SWING, 1.0, tol)
                    p.ext = True
                    ev["major"] |= self.announce(p)

            # 4) sweeps / tests / taken
            mode = P["sweepMode"]
            pen = 0.0 if mode == "Aggressive" else tol
            rejDn, rejUp = (h - c) >= 0.5 * (h - l), (c - l) >= 0.5 * (h - l)
            for k in range(len(self.pools) - 1, -1, -1):
                p = self.pools[k]
                outcome = 0
                if p.isBuy:
                    if c > p.price + pen:
                        outcome = 2
                    elif P["enableSweeps"] and h > p.price + pen and c <= p.price and (mode != "Strict" or rejDn):
                        outcome = 1
                    elif h >= p.price - tol and i - p.b > L and (p.lastTest is None or i - p.lastTest >= L):
                        p.tests, p.lastTest, p.fresh = p.tests + 1, i, i
                else:
                    if c < p.price - pen:
                        outcome = 2
                    elif P["enableSweeps"] and l < p.price - pen and c >= p.price and (mode != "Strict" or rejUp):
                        outcome = 1
                    elif l <= p.price + tol and i - p.b > L and (p.lastTest is None or i - p.lastTest >= L):
                        p.tests, p.lastTest, p.fresh = p.tests + 1, i, i
                if outcome == 1:
                    p.alive, p.sweptB = False, i
                    ev["bslSweep" if p.isBuy else "sslSweep"] = True
                    self.pools.pop(k)
                    if P["keepSwept"] or not P["removeSwept"]:
                        self.swept.append(p)
                elif outcome == 2:
                    p.alive = False
                    self.pools.pop(k)
                    ev["taken"] += 1
            while len(self.swept) > P["maxSweeps"]:
                self.swept.pop(0)

            # 5) structure
            if not shBroken and lastSH is not None and c > lastSH + pen:
                shBroken, structDir, lastBullShiftB, ev["bos"] = True, 1, i, 1
                if lastSLPool is not None and lastSLPool.alive:
                    lastSLPool.structural = True
                    ev["major"] |= self.announce(lastSLPool)
            if not slBroken and lastSL is not None and c < lastSL - pen:
                slBroken, structDir, lastBearShiftB, ev["bos"] = True, -1, i, -1
                if lastSHPool is not None and lastSHPool.alive:
                    lastSHPool.structural = True
                    ev["major"] |= self.announce(lastSHPool)
            self.enforce_cap(i)

            # ── scoring ─────────────────────────────────────────────────────
            rng = h - l
            clv = (2 * c - h - l) / rng if rng > 0 else 0.0
            bodyN = clamp((c - o) / self.atr, -1, 1)
            pl_ = P["pressLen"]
            rocN = clamp((c - (self.c[i - pl_] if i >= pl_ else c)) / (self.atr * math.sqrt(pl_)), -1, 1)
            up = h - self.h[i - 1] if i else 0.0
            dn = self.l[i - 1] - l if i else 0.0
            trr = dmi_tr.update(tr)
            pdm = dmi_p.update(up if (up > dn and up > 0) else 0.0)
            mdm = dmi_m.update(dn if (dn > up and dn > 0) else 0.0)
            if trr:
                dip, dim = 100 * pdm / trr, 100 * mdm / trr
                dmiN = (dip - dim) / (dip + dim) if dip + dim > 0 else 0.0
            else:
                dmiN = 0.0
            pressRaw = (clv + bodyN + rocN + dmiN) / 4.0
            pe = pressEma.update(pressRaw)
            pressure = clamp(pe if pe is not None else pressRaw, -1, 1)

            mode_f = P["flowMode"]
            useS = mode_f in ("Liquidity + Structure", "Balanced")
            useP = mode_f in ("Liquidity + Pressure", "Balanced")
            kM = 0.5 if mode_f == "Balanced" else 1.0
            bM = sM = 1.0
            if useS and structDir != 0:
                st = 0.25 * clamp(P["structWeight"], 0, 1) * kM
                if structDir == 1:
                    bM *= 1 + st
                else:
                    sM *= 1 + st
            if useP:
                pt = 0.25 * clamp(P["pressWeight"], 0, 1) * kM * abs(pressure)
                if pressure > 0:
                    bM *= 1 + pt
                else:
                    sM *= 1 + pt
            if P["usePD"] and mode_f != "Liquidity Only":
                pdPos = clamp((c - rangeLo) / (rangeHi - rangeLo), 0, 1) if rangeHi > rangeLo else 0.5
                pdt = 0.25 * P["pdWeight"] * abs(pdPos - 0.5) * 2
                if pdPos > 0.5:
                    sM *= 1 + pdt
                else:
                    bM *= 1 + pdt

            buyRaw = sellRaw = buyAdj = sellAdj = 0.0
            buyCnt = sellCnt = 0
            bestBuy = bestSell = None
            bestBuyW = bestSellW = 0.0
            for p in self.pools:
                p.w = 0.0
                p.dAtr = abs(p.price - c) / self.atr
                if ((p.isBuy and p.price > c) or (not p.isBuy and p.price < c)) and p.dAtr <= P["maxDistATR"]:
                    s = self.intrinsic(p)
                    if s >= P["minPoolStr"]:
                        w0 = s * self.time_factor(i - p.fresh) * self.dist_w(p.dAtr)
                        w = w0 * (bM if p.isBuy else sM)
                        p.w = w
                        if p.isBuy:
                            buyRaw += w0; buyAdj += w; buyCnt += 1
                            if w > bestBuyW:
                                bestBuyW, bestBuy = w, p
                        else:
                            sellRaw += w0; sellAdj += w; sellCnt += 1
                            if w > bestSellW:
                                bestSellW, bestSell = w, p
            if not P["removeSwept"]:
                for p in self.swept:
                    d = abs(p.price - c) / self.atr
                    if ((p.isBuy and p.price > c) or (not p.isBuy and p.price < c)) and d <= P["maxDistATR"]:
                        s = self.intrinsic(p)
                        if s >= P["minPoolStr"]:
                            w0 = 0.5 * s * self.time_factor(i - p.fresh) * self.dist_w(d)
                            if p.isBuy:
                                buyRaw += w0; buyAdj += w0 * bM
                            else:
                                sellRaw += w0; sellAdj += w0 * sM
            eb, es = emaB.update(buyAdj), emaS.update(sellAdj)
            buySm = eb if eb is not None else buyAdj
            sellSm = es if es is not None else sellAdj
            tot = buySm + sellSm
            den = tot + 2 * P["stability"]
            pctModel = (buySm + P["stability"]) / den * 100 if den > 0 else 50.0
            warm = i >= L * 4 + P["atrLen"]
            dataFrac = 0.0 if (not warm or buyCnt + sellCnt == 0) else min(tot / 0.6, 1.0)
            buyPct = 50.0 + (pctModel - 50.0) * dataFrac
            lowData = dataFrac < 1.0
            diff = 2 * buyPct - 100
            dom = 0 if lowData else (1 if diff > 0 and diff >= P["balanceThr"] else -1 if diff < 0 and -diff >= P["balanceThr"] else 0)
            buyPctHist.append(buyPct)

            # events
            flip = 0
            if dom != domState:
                domState = dom
            if dom != 0 and dom != lastDirSide:
                if lastDirSide != 0:
                    flip = dom
                lastDirSide = dom
            sl = P["shiftLook"]
            chg = buyPct - (buyPctHist[i - sl] if i >= sl else buyPct)
            shift = 0
            if not lowData and abs(chg) >= P["shiftThr"] and (lastShiftB is None or i - lastShiftB > sl):
                shift, lastShiftB = (1 if chg > 0 else -1), i
            buyPrev = buyPctHist[i - 1] if i else buyPct
            if ev["sslSweep"]:
                lastSSLSweepB, buyBaseAtSSL = i, buyPrev
            if ev["bslSweep"]:
                lastBSLSweepB, sellBaseAtBSL = i, 100 - buyPrev
            sig = 0
            if P["enableSig"] and not lowData:
                W = P["sigWindow"]
                if (lastSSLSweepB is not None and i - lastSSLSweepB <= W and lastBullShiftB is not None
                        and i - lastBullShiftB <= W and lastBullShiftB >= lastSSLSweepB
                        and buyPct >= P["sigThr"] and buyPct > buyBaseAtSSL and buyCnt > 0
                        and lastSSLSweepB != lastBuySigAnchor):
                    sig, lastBuySigAnchor = 1, lastSSLSweepB
                sellPct = 100 - buyPct
                if (lastBSLSweepB is not None and i - lastBSLSweepB <= W and lastBearShiftB is not None
                        and i - lastBearShiftB <= W and lastBearShiftB >= lastBSLSweepB
                        and sellPct >= P["sigThr"] and sellPct > sellBaseAtBSL and sellCnt > 0
                        and lastBSLSweepB != lastSellSigAnchor):
                    sig, lastSellSigAnchor = -1, lastBSLSweepB
            key = bestBuy if dom == 1 else bestSell if dom == -1 else (bestBuy if bestBuyW >= bestSellW else bestSell)
            out.append(dict(ev, buyPct=buyPct, disp=round(buyPct), dom=dom, lowData=lowData, flip=flip, shift=shift,
                            sig=sig, buyRaw=buyRaw, sellRaw=sellRaw, buyCnt=buyCnt, sellCnt=sellCnt, close=c,
                            key=(key.price, key.isBuy, round(self.intrinsic(key), 2)) if key else None,
                            pools=[(round(q.price, 2), q.isBuy, q.members, q.tests, round(self.intrinsic(q), 2)) for q in self.pools]))
        return out


# ── synthetic price paths ──────────────────────────────────────────────────
def path_bars(waypoints, noise=0.05, seed=1, vol=1000.0):
    """Piecewise-linear close path through (bar, price) waypoints -> OHLCV bars.
    Wicks are small and deterministic so swing extremes land exactly on waypoints."""
    rnd = random.Random(seed)
    closes = []
    for (b0, p0), (b1, p1) in zip(waypoints, waypoints[1:]):
        for b in range(b0, b1):
            t = (b - b0) / (b1 - b0)
            closes.append(p0 + (p1 - p0) * t)
    closes.append(waypoints[-1][1])
    bars = []
    for k, c in enumerate(closes):
        o = closes[k - 1] if k else c
        jitter = noise * rnd.random() * 0.2
        h = max(o, c) + jitter
        l = min(o, c) - jitter
        bars.append((o, h, l, c, vol * (0.8 + 0.4 * rnd.random())))
    return bars


def set_bar(bars, k, o=None, h=None, l=None, c=None):
    bo, bh, bl, bc, bv = bars[k]
    o = bo if o is None else o
    c = bc if c is None else c
    h = max(bh if h is None else h, o, c)
    l = min(bl if l is None else l, o, c)
    bars[k] = (o, h, l, c, bv)


def random_walk(n, seed, vol=1.0, drift=0.0):
    rnd = random.Random(seed)
    bars, c = [], 100.0
    for _ in range(n):
        o = c
        c = o + drift + rnd.gauss(0, vol)
        h = max(o, c) + abs(rnd.gauss(0, vol * 0.5))
        l = min(o, c) - abs(rnd.gauss(0, vol * 0.5))
        bars.append((o, h, l, c, 1000 * (0.5 + rnd.random())))
    return bars


# ── scenarios from the build spec (§66) + stability checks ─────────────────
def swing_bars(waypoints, sigma=0.35, seed=1, L=5):
    """Realistic noisy OHLC bars through (bar, price, kind) waypoints.
    kind 'H' / 'L' pins an exact swing high / low at that bar (neighbouring bars
    are kept strictly inside it), so the pool prices in a scenario are known."""
    rnd = random.Random(seed)
    closes = []
    for (b0, p0, _), (b1, p1, _) in zip(waypoints, waypoints[1:]):
        for b in range(b0, b1):
            closes.append(p0 + (p1 - p0) * (b - b0) / (b1 - b0) + rnd.gauss(0, sigma))
    closes.append(waypoints[-1][1])
    bars = []
    for k, c in enumerate(closes):
        o = closes[k - 1] if k else c
        bars.append([o, max(o, c) + abs(rnd.gauss(0, sigma)), min(o, c) - abs(rnd.gauss(0, sigma)), c,
                     1000 * (0.7 + 0.6 * rnd.random())])
    for b, v, kind in waypoints:
        if kind not in ("H", "L"):
            continue
        sgn = 1 if kind == "H" else -1
        for j in range(max(0, b - L - 2), min(len(bars), b + L + 3)):
            o, h, l, c, vol = bars[j]
            if j == b:
                c = v - sgn * 0.6 * sigma
                o = min(o, v - 0.1) if sgn == 1 else max(o, v + 0.1)
                h, l = (v, min(l, o, c)) if sgn == 1 else (max(h, o, c), v)
            else:
                cap = v - sgn * 0.12
                if sgn == 1:
                    o, c = min(o, cap), min(c, cap)
                    h, l = min(max(h, o, c), cap), min(l, o, c)
                else:
                    o, c = max(o, cap), max(c, cap)
                    h, l = max(h, o, c), max(min(l, o, c), cap)
            bars[j] = [o, h, l, c, vol]
    return [tuple(b) for b in bars]


def mirror(bars, axis=210.0):
    """Reflect a path vertically: highs become lows (buy-side <-> sell-side)."""
    return [(axis - o, axis - l, axis - h, axis - c, v) for o, h, l, c, v in bars]


def last(out):
    return out[-1]


# A (spec): strong equal highs above price, weak (minor, single) lows below
EQH_SPEC = [(0, 100, None), (10, 106, None), (16, 110.00, "H"), (24, 107.6, "L"), (32, 110.05, "H"),
            (40, 107.9, "L"), (48, 109.96, "H"), (58, 108.6, None)]
# A2 (harder, realistic): triple top vs two MAJOR higher lows that sit closer to price
EQH = [(0, 100, None), (15, 110.00, "H"), (30, 103.5, "L"), (45, 110.05, "H"), (60, 104.5, "L"),
       (75, 109.96, "H"), (95, 106, None)]
CTRL = [(0, 100, None), (15, 110.00, "H"), (30, 103.5, "L"), (45, 111.60, "H"), (60, 104.5, "L"),
        (75, 108.30, "H"), (95, 106, None)]
BOTH = [(0, 105, None), (12, 110.00, "H"), (24, 100.00, "L"), (36, 110.04, "H"), (48, 100.03, "L"),
        (60, 109.97, "H"), (72, 99.96, "L"), (84, 105, None)]


def run_scenarios(verbose=True, **kw):
    results = []

    def check(name, cond, detail):
        results.append((name, bool(cond), detail))
        if verbose:
            print(f"[{'PASS' if cond else 'FAIL'}] {name}: {detail}")

    thr = 50 + DEFAULTS["balanceThr"]
    bS = swing_bars(EQH_SPEC)
    for mode in ("Liquidity Only", "Liquidity + Structure"):
        a = last(Model(bS, flowMode=mode, **kw).run())
        eqp = [p for p in a["pools"] if p[1] and p[2] >= 3]
        check(f"A  strong equal highs above, weak lows below -> buy-side dominant ({mode})",
              a["buyPct"] >= thr and a["dom"] == 1 and eqp, f"BUY {a['buyPct']:.1f}% (dom {a['dom']}), cluster {eqp}")
    b = last(Model(mirror(bS), **kw).run())
    check("B  strong equal lows below, weak highs above -> sell-side dominant",
          100 - b["buyPct"] >= thr and b["dom"] == -1, f"SELL {100 - b['buyPct']:.1f}% (dom {b['dom']})")
    aS = last(Model(bS, **kw).run())
    check("B' model is symmetric (A mirrored == B)", abs(aS["buyPct"] - (100 - b["buyPct"])) < 1e-6,
          f"{aS['buyPct']:.4f} vs {100 - b['buyPct']:.4f}")

    bA = swing_bars(EQH)
    a2 = last(Model(bA, flowMode="Liquidity Only", **kw).run())
    ct = last(Model(swing_bars(CTRL), flowMode="Liquidity Only", **kw).run())
    check("A2 clustering adds liquidity: equal highs beat the same highs un-clustered",
          a2["buyPct"] - ct["buyPct"] >= 5, f"clustered BUY {a2['buyPct']:.1f}% vs control {ct['buyPct']:.1f}% (Liquidity Only)")
    check("A2 triple top outweighs two closer major lows (Liquidity Only)", a2["buyPct"] > 50,
          f"BUY {a2['buyPct']:.1f}%, key {a2['key']}")

    # C: after A2, price rallies into the equal highs, runs them and closes back below
    wC = EQH[:-1] + [(95, 106, None), (104, 109.3, None), (112, 107.5, None)]
    bC = swing_bars(wC)
    k = 104
    o_, h_, l_, c_, v_ = bC[k]
    bC[k] = (109.3, 110.75, 109.0, 109.35, v_)          # wick 0.7 above the cluster, close back below
    oC = Model(bC, **kw).run()
    before, at, after = oC[k - 1], oC[k], last(oC)
    cl_before = [p for p in before["pools"] if p[1] and p[2] >= 3]
    cl_after = [p for p in after["pools"] if p[1] and p[2] >= 2 and abs(p[0] - 110.05) < 0.2]
    check("C  buy-side sweep is detected on the confirmed candle", at["bslSweep"] and cl_before,
          f"sweep flag on bar {k}: {at['bslSweep']}, cluster before {cl_before}")
    check("C' swept equal highs leave the active score", not cl_after and at["buyRaw"] < before["buyRaw"] * 0.5,
          f"raw buy {before['buyRaw']:.2f} -> {at['buyRaw']:.2f} on the sweep bar; BUY {before['buyPct']:.1f}% -> {after['buyPct']:.1f}%")

    oD = Model(mirror(bC), **kw).run()
    check("D  sell-side sweep mirrors C", oD[k]["sslSweep"] and abs(last(oD)["buyPct"] - (100 - after["buyPct"])) < 1e-6,
          f"sweep {oD[k]['sslSweep']}, SELL after {100 - last(oD)['buyPct']:.1f}%")

    e = last(Model(swing_bars(BOTH), **kw).run())
    check("E  strong liquidity on both sides -> near balanced", abs(e["buyPct"] - 50) <= 12,
          f"BUY {e['buyPct']:.1f}% / SELL {100 - e['buyPct']:.1f}% (dom {e['dom']})")

    f = last(Model(swing_bars([(0, 100, None), (12, 101, None)]), **kw).run())
    check("F  no meaningful data -> LOW DATA, 50/50", f["lowData"] and abs(f["buyPct"] - 50) < 1e-9,
          f"lowData {f['lowData']}, BUY {f['buyPct']:.1f}%")
    f2 = last(Model([(100, 100, 100, 100, 0)] * 200, **kw).run())
    check("F' flat market (zero range, no volume) -> LOW DATA", f2["lowData"] and abs(f2["buyPct"] - 50) < 1e-9,
          f"lowData {f2['lowData']}, BUY {f2['buyPct']:.1f}%")

    # G: one giant green candle must not turn a sell-side reading into an extreme buy-side one
    for mode in ("Liquidity + Structure", "Liquidity + Pressure", "Balanced"):
        bG = mirror(bS)
        base = last(Model(bG, flowMode=mode).run())
        cG = bG[-1][3]
        g = last(Model(list(bG) + [(cG, cG + 2.0, cG - 0.05, cG + 1.9, 5000.0)], flowMode=mode).run())
        check(f"G  giant green candle stays bounded ({mode})", base["dom"] == -1 and g["buyPct"] < 75,
              f"SELL {100 - base['buyPct']:.1f}% -> BUY {g['buyPct']:.1f}% after a ~2 ATR candle")
    return results


def random_walk_stats(seeds=range(1, 7), n=3000, verbose=True, **kw):
    agg = dict(bars=0, extreme=0, balanced=0, low=0, flips=0, shifts=0, sweeps=0, sigs=0, absstep=0.0, maxstep=0.0)
    for s in seeds:
        out = Model(random_walk(n, s), enableSig=True, **kw).run()
        prev = None
        for r in out[100:]:
            agg["bars"] += 1
            agg["extreme"] += max(r["buyPct"], 100 - r["buyPct"]) >= DEFAULTS["extremeLvl"]
            agg["balanced"] += r["dom"] == 0 and not r["lowData"]
            agg["low"] += r["lowData"]
            agg["flips"] += r["flip"] != 0
            agg["shifts"] += r["shift"] != 0
            agg["sweeps"] += r["bslSweep"] + r["sslSweep"]
            agg["sigs"] += r["sig"] != 0
            if prev is not None:
                st = abs(r["buyPct"] - prev)
                agg["absstep"] += st
                agg["maxstep"] = max(agg["maxstep"], st)
            prev = r["buyPct"]
    B = agg["bars"]
    stats = dict(
        extreme_pct=100 * agg["extreme"] / B, balanced_pct=100 * agg["balanced"] / B, lowdata_pct=100 * agg["low"] / B,
        flips_per_1000=1000 * agg["flips"] / B, shifts_per_1000=1000 * agg["shifts"] / B,
        sweeps_per_1000=1000 * agg["sweeps"] / B, signals_per_1000=1000 * agg["sigs"] / B,
        mean_abs_step=agg["absstep"] / B, max_step=agg["maxstep"])
    if verbose:
        print("random walks:", ", ".join(f"{k}={v:.2f}" for k, v in stats.items()))
    return stats


if __name__ == "__main__":
    res = run_scenarios()
    print()
    random_walk_stats()
    failed = [r for r in res if not r[1]]
    print(f"\n{len(res) - len(failed)}/{len(res)} scenario checks passed")
    raise SystemExit(1 if failed else 0)
