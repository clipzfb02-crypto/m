# Extension (declared exploratory, written after H1/H2 results but before any H3-H6 transfer result was seen):
# can ONE universal reach curve, with no per-instrument intercept, be calibrated on an instrument it never saw?
# This is the form a Pine script can carry. Rows = pool targets (SW/SES/PD/PW) at 0.25-6 ATR, outcome = strict
# trade-through within 60 bars (the H3 table).
# Candidates, all fitted on IS rows only:
#   RAND  : the distance-matched random-level surface of the held-out instrument's own IS (P(reach | d) from random starts)
#   U2    : logit(p) = a + b1*log d + b2*(log d)^2 + c*lvr + e*side, fitted on the OTHER instruments' IS rows (leave-one-out)
#   U2own : same compact form fitted on the instrument's own IS rows
#   BASEown: spline BASE fitted on the instrument's own IS rows
# Scored on the held-out instrument's OOS rows: Brier, calibration-in-the-large (mean pred - obs), ECE (10 bins), AUC.
import sys, json
import numpy as np, pandas as pd
import e3lib as L
import models as M

OUT = L.OUT
lines, res = [], {}


def log(s):
    print(s, flush=True); lines.append(s)


def compact(D):
    x = np.log(D.d.values)
    return np.column_stack([np.ones(len(D)), x, x * x, D.lvr.values, D.side.values.astype(float)])


for tf in ("1h", "5m"):
    R, T, Lb = M.load_tf(tf)
    P = R[R.kind != L.FVG].reset_index(drop=True)
    log(f"\n##### {tf}: pool rows {len(P)}; columns: compact = [1, log d, (log d)^2, lvr, side]")
    # pooled compact fit (all instruments' IS) -> coefficients a Pine script could carry
    ism = P.is_.values
    rp = M.fit(compact(P[ism]), P.hit60.values[ism].astype(float), groups=P.dk.values[ism])
    res[f"{tf}|compact_pooled_IS_coefs"] = dict(zip(["a", "b_logd", "b_logd2", "c_lvr", "e_side"], map(float, rp.params)))
    res[f"{tf}|compact_pooled_IS_se"] = dict(zip(["a", "b_logd", "b_logd2", "c_lvr", "e_side"], map(float, rp.bse)))
    log(f"  pooled compact IS coefs: " + ", ".join(f"{k}={v:+.4f} (se {res[f'{tf}|compact_pooled_IS_se'][k]:.4f})" for k, v in res[f"{tf}|compact_pooled_IS_coefs"].items()))
    for ds in sorted(P.ds.unique()):
        me = (P.ds.values == ds)
        tr = (~me) & ism
        te = me & P.oos.values
        if te.sum() < 500:
            log(f"  {ds}: OOS rows {te.sum()} < 500, skipped")
            continue
        y = P.hit60.values[te].astype(float)
        r_u = M.fit(compact(P[tr]), P.hit60.values[tr].astype(float))
        r_o = M.fit(compact(P[me & ism]), P.hit60.values[me & ism].astype(float))
        sub = P[me].reset_index(drop=True)
        des = M.Design(sub, sub.is_.values)
        Xb, _ = des.base()
        r_b = M.fit(Xb[sub.is_.values], sub.hit60.values[sub.is_.values].astype(float))
        preds = {"RAND": np.clip(P.p_rand_strict.values[te], 1e-6, 1 - 1e-6),
                 "U2(leave-one-out)": M.predict(r_u, compact(P[te])),
                 "U2own": M.predict(r_o, compact(P[te])),
                 "BASEown": M.predict(r_b, Xb[sub.oos.values])}
        B = M.Boot(P.dk.values[te], Lb, nrep=1000, nrep_auc=1, seed=51)
        out = {}
        for k, p in preds.items():
            _, ece = M.calib_table(p, y)
            out[k] = dict(brier=float(M.brier(p, y).mean()), citl=float(p.mean() - y.mean()), ece=float(ece), auc=float(M.auc(p, y)))
        # bootstrap CI of Brier difference: universal leave-one-out vs own-instrument BASE
        m_, lo_, hi_, _ = B.mean(M.brier(preds["U2(leave-one-out)"], y) - M.brier(preds["BASEown"], y))
        m2, lo2, hi2, _ = B.mean(M.brier(preds["RAND"], y) - M.brier(preds["BASEown"], y))
        res[f"{tf}|{ds}"] = dict(n=int(te.sum()), obs=float(y.mean()), models=out,
                                 dBrier_U2loo_minus_BASEown=(float(m_), float(lo_), float(hi_)),
                                 dBrier_RAND_minus_BASEown=(float(m2), float(lo2), float(hi2)))
        log(f"  {ds:4s} OOS n={te.sum():6d} obs={y.mean():.4f} | " + " | ".join(
            f"{k}: Brier {v['brier']:.4f} CITL {v['citl']:+.4f} ECE {v['ece']:.4f} AUC {v['auc']:.4f}" for k, v in out.items()))
        log(f"        Brier(U2 loo) - Brier(BASEown) = {m_:+.5f} [{lo_:+.5f},{hi_:+.5f}];  Brier(RAND) - Brier(BASEown) = {m2:+.5f} [{lo2:+.5f},{hi2:+.5f}]")

open(OUT + "transfer_results.txt", "w").write("\n".join(lines))
json.dump(res, open(OUT + "transfer_results.json", "w"), indent=1, default=lambda x: float(x) if np.isscalar(x) else list(x))
