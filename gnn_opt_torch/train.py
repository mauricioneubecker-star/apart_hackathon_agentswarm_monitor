#!/usr/bin/env python3
"""Train / cross-validate the spatio-temporal GNN monitor on the gnn_opt harness folds.

  # CV on all 18 harness folds (2x5 grouped ID + 8 LODO), writes gnn_opt_torch/preds/cv/<name>.csv
  python3 gnn_opt_torch/train.py --data gnn_opt_data/night --cfg '{"conv":"rgine"}' --name rgine --cv all
  # screening on a subset of folds: --cv id0 (5 folds) | lodo | id | all
  # final model on all of night_train, predictions for every snapshot of --data (eval file)
  python3 gnn_opt_torch/train.py --data gnn_opt_data/night --cfg cfg.json --name best --eval
  # controls: --control rewire | shuffle_ef | shuffle_labels

Config keys (defaults in DEFAULT): model (see model.STGNN) + training (epochs, lr, wd, batch_runs, pos_weight,
focal_gamma, w_aux, w_risk, w_node, edge_drop, feat_noise, swa_last, swa, swa_lr, seeds, feat).
swa=0: the last `swa_last` epochs of the one-cycle schedule are a prediction (snapshot) ensemble.
swa=1: one-cycle over the first epochs - swa_last epochs, then a constant lr = swa_lr * lr for swa_last epochs whose
weights are averaged (stochastic weight averaging; no BatchNorm in the model, so no statistics update is needed).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from model import STGNN  # noqa: E402
from tdata import Data  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, ".."))
FOLDS = os.path.join(REPO, "gnn_opt", "folds.json")
TRAIN_SPLIT = "night_train"

DEFAULT = dict(hid=64, layers=3, conv="rgine", reverse=True, vn=True, tmem="none", tmem_at=1, gtemp="gru", drop=0.1,
               heads=4, aggr=["sum", "mean", "max"], edge_readout=True, att_pool=True, edge_update=True,
               epochs=40, lr=2e-3, wd=1e-4, batch_runs=8, pos_weight=3.0, focal_gamma=0.0, w_aux=0.5, w_risk=0.2,
               w_node=0.5, edge_drop=0.1, feat_noise=0.05, swa_last=8, seeds=1, feat="headline", clock=False,
               label_smooth=0.0, judge_aug=0.0, crop=0, swa=0, swa_lr=0.25, test_judge=-1)

_D = {}


def get_data(path, feat, clock):
    key = (path, feat, clock)
    if key not in _D:
        _D[key] = Data(path, feat, clock)
    return _D[key]


def bce(logit, y, pw=1.0, gamma=0.0, ls=0.0):
    m = ~torch.isnan(y)
    if m.sum() == 0:
        return logit.sum() * 0
    lg, yy = logit[m], y[m]
    if ls > 0:
        yy = yy * (1 - ls) + 0.5 * ls
    w = torch.where(yy > 0.5, torch.full_like(yy, pw), torch.ones_like(yy))
    l = F.binary_cross_entropy_with_logits(lg, yy, reduction="none")
    if gamma > 0:
        p = torch.sigmoid(lg)
        pt = torch.where(yy > 0.5, p, 1 - p)
        l = l * (1 - pt).pow(gamma)
    return (w * l).sum() / w.sum()


def crop_run(r, k):
    if k <= 0:
        return r
    return {**r, "snaps": r["snaps"][k:], "tab": r["tab"][:, k:]}


def fit_models(data_path, cfg, train_runs_idx, seed=0, control=None, verbose=False, keep_states=False,
               pred_runs_idx=None):
    """Train cfg['seeds'] models; returns (snapshot-ensembled predictions for pred_runs_idx, saved states)."""
    torch.set_num_threads(1)
    c = {**DEFAULT, **cfg}
    D = get_data(data_path, c["feat"], c["clock"])
    if (c["judge_aug"] > 0 or c["test_judge"] >= 0) and not D.alt:
        for j in ("night_ds", "night_hk"):
            D.add_judge(os.path.join(os.path.dirname(os.path.normpath(data_path)), j))
    tr = [D.runs[i] for i in train_runs_idx]
    D.fit_norm(tr)
    # input controls corrupt the prediction batch too (otherwise the test graphs still carry the real structure)
    pgen = torch.Generator().manual_seed(seed * 1000 + 999)
    pb = (D.batch([D.runs[i] for i in pred_runs_idx], pgen, rewire=(control == "rewire"),
                  shuffle_ef=(control == "shuffle_ef"), judge=c["test_judge"])
          if pred_runs_idx is not None else None)   # test_judge: 0 = DeepSeek only, 1 = Haiku only (judge swap)
    preds, states = [], []
    for s in range(c["seeds"]):
        sd = seed * 1000 + s
        torch.manual_seed(sd)
        np.random.seed(sd)
        gen = torch.Generator().manual_seed(sd)
        model = STGNN(D.d_node, D.d_edge, **c)
        opt = torch.optim.AdamW(model.parameters(), lr=c["lr"], weight_decay=c["wd"])
        n_one = c["epochs"] - (c["swa_last"] if c["swa"] else 0)
        steps = n_one * int(np.ceil(len(tr) / c["batch_runs"]))
        sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=c["lr"], total_steps=steps, pct_start=0.15)
        swa_model = torch.optim.swa_utils.AveragedModel(model) if c["swa"] else None
        # shuffled-labels control: training runs get the label sequences of other training runs
        perm_lab = np.random.RandomState(sd).permutation(len(tr)) if control == "shuffle_labels" else None
        acc, n_acc = None, 0
        for ep in range(c["epochs"]):
            model.train()
            order = np.random.permutation(len(tr))
            tot = 0.0
            for i in range(0, len(tr), c["batch_runs"]):
                bi = order[i:i + c["batch_runs"]]
                jd = int(np.random.randint(len(D.alt))) if (D.alt and np.random.rand() < c["judge_aug"]) else -1
                runs_b = [tr[j] for j in bi]
                if c["crop"] > 0:     # random start-crop: the temporal block cannot rely on the episode start
                    runs_b = [crop_run(r, np.random.randint(0, c["crop"] + 1)) for r in runs_b]
                b = D.batch(runs_b, gen, c["edge_drop"], c["feat_noise"],
                            rewire=(control == "rewire"), shuffle_ef=(control == "shuffle_ef"), judge=jd)
                if perm_lab is not None:
                    lb = D.batch([tr[perm_lab[j]] for j in bi])
                    for k in ("y3", "y5", "yrel3", "risk"):
                        b[k] = lb[k]
                    b["nlab"] = torch.full_like(b["nlab"], float("nan"))
                og, on, _ = model(b)
                loss = bce(og[:, 0], b["y3"], c["pos_weight"], c["focal_gamma"], c["label_smooth"])
                if c["w_aux"] > 0:
                    loss = loss + c["w_aux"] * (bce(og[:, 1], b["y5"], c["pos_weight"]) + bce(og[:, 2], b["yrel3"], c["pos_weight"]))
                if c["w_risk"] > 0:
                    loss = loss + c["w_risk"] * F.poisson_nll_loss(og[:, 3], b["risk"], log_input=True)
                if c["w_node"] > 0:
                    nm = b["next"] < 0.5
                    loss = loss + c["w_node"] * (bce(on[nm, 0], b["nlab"][nm, 0]) + bce(on[nm, 1], b["nlab"][nm, 1], 3.0))
                opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                if ep < n_one:
                    sched.step()
                tot += float(loss.detach())
            if swa_model is not None:
                if ep == n_one - 1:
                    for g in opt.param_groups:
                        g["lr"] = c["swa_lr"] * c["lr"]
                if ep >= n_one:
                    swa_model.update_parameters(model)
                continue_ = True
            else:
                continue_ = False
            if not continue_ and ep >= c["epochs"] - c["swa_last"]:
                if keep_states:
                    states.append({k: v.detach().clone() for k, v in model.state_dict().items()})
                if pb is not None:
                    model.eval()
                    with torch.no_grad():
                        og, _, _ = model(pb)
                    p = torch.stack([torch.sigmoid(og[:, 0]), og[:, 3].exp()], 1)
                    acc = p if acc is None else acc + p
                    n_acc += 1
            if verbose:
                print(f"  seed {s} ep {ep} loss {tot:.3f}", flush=True)
        if swa_model is not None:
            sm = swa_model.module
            if keep_states:
                states.append({k: v.detach().clone() for k, v in sm.state_dict().items()})
            if pb is not None:
                sm.eval()
                with torch.no_grad():
                    og, _, _ = sm(pb)
                acc, n_acc = torch.stack([torch.sigmoid(og[:, 0]), og[:, 3].exp()], 1), 1
        if pb is not None:
            preds.append(acc / n_acc)
    out = None
    if pb is not None:
        P = torch.stack(preds).mean(0).numpy()
        snaps = pb["snaps"].numpy()
        S = D.S
        out = pd.DataFrame({"run": S.run.values[snaps], "round": S["round"].values[snaps], "score": P[:, 0],
                            "count": P[:, 1]})
    norm = {"xm": D.xm, "xs": D.xs, "em": D.em_, "es": D.es_, "e_names": D.e_names, "n_names": D.n_names}
    return out, states, norm


def fit_predict(data_path, cfg, train_runs_idx, pred_runs_idx, seed=0, control=None, verbose=False):
    return fit_models(data_path, cfg, train_runs_idx, seed, control, verbose, pred_runs_idx=pred_runs_idx)[0]


def predict_states(D, cfg, states, norm, runs_idx=None):
    """Apply saved snapshot/seed ensemble to Data D (normalisation from training)."""
    c = {**DEFAULT, **cfg}
    assert D.e_names == norm["e_names"] and D.n_names == norm["n_names"], "feature columns differ"
    D.xm, D.xs, D.em_, D.es_ = norm["xm"], norm["xs"], norm["em"], norm["es"]
    runs_idx = list(range(len(D.runs))) if runs_idx is None else runs_idx
    pb = D.batch([D.runs[i] for i in runs_idx])
    model = STGNN(D.d_node, D.d_edge, **c)
    acc = 0
    for st in states:
        model.load_state_dict(st)
        model.eval()
        with torch.no_grad():
            og, _, _ = model(pb)
        acc = acc + torch.stack([torch.sigmoid(og[:, 0]), og[:, 3].exp()], 1)
    P = (acc / len(states)).numpy()
    snaps = pb["snaps"].numpy()
    return pd.DataFrame({"run": D.S.run.values[snaps], "round": D.S["round"].values[snaps], "score": P[:, 0],
                         "count": P[:, 1]})


def _job(args):
    data_path, cfg, tr_idx, te_idx, seed, control, fold = args
    t0 = time.time()
    df = fit_predict(data_path, cfg, tr_idx, te_idx, seed, control)
    df["fold"] = fold
    return df, time.time() - t0


def cv_jobs(D, which, seed_base=0):
    F_ = json.load(open(FOLDS))
    kinds = {"all": ["id", "lodo"], "id": ["id"], "lodo": ["lodo"], "id0": ["id0"], "id0+lodo": ["id0", "lodo"]}[which]
    tr_runs = [i for i, r in enumerate(D.runs) if r["split"] == TRAIN_SPLIT]
    jobs = []
    for kind in kinds:
        folds = F_["lodo"] if kind == "lodo" else {k: v for k, v in F_["id"].items() if kind == "id" or k.startswith("id0")}
        for name, te_cfgs in folds.items():
            te_cfgs = set(te_cfgs)
            tr = [i for i in tr_runs if D.runs[i]["cfg"] not in te_cfgs]
            te = [i for i in tr_runs if D.runs[i]["cfg"] in te_cfgs]
            jobs.append((name, tr, te))
    return jobs


def run_cv(data_path, cfg, which="all", workers=4, control=None, seed=0):
    c = {**DEFAULT, **cfg}
    D = get_data(data_path, c["feat"], c["clock"])
    jobs = cv_jobs(D, which)
    args = [(data_path, cfg, tr, te, seed + k, control, name) for k, (name, tr, te) in enumerate(jobs)]
    out = []
    if workers <= 1:
        for a in args:
            out.append(_job(a))
    else:
        with ProcessPoolExecutor(workers) as ex:
            out = list(ex.map(_job, args))
    P = pd.concat([o[0] for o in out], ignore_index=True)
    # keep the harness training rows only (eval == 1 and label defined) -> identical rows as the baselines
    S = D.S
    keep = S[(S.split == TRAIN_SPLIT) & (S["eval"] == 1) & S.y3.notna()][["run", "round"]]
    P = P.merge(keep, on=["run", "round"], how="inner")
    return P, sum(o[1] for o in out)


def summarize(data_path, P):
    sys.path.insert(0, os.path.join(REPO, "gnn_opt"))
    import harness as H
    S = pd.read_csv(os.path.join(data_path, "snapshots.csv"), low_memory=False)
    r = H.cv_summary(S, P)
    lodo = r.get("lodo", {})
    return {"select": r.get("select"), "id_auroc": r["id_auroc"], "id_auprc": r["id_auprc"],
            "lodo_mean": r.get("lodo_mean"), "lodo_min": r.get("lodo_min"),
            **{k.replace("hold_", "L:"): round(v, 4) for k, v in lodo.items()}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(REPO, "gnn_opt_data", "night"))
    ap.add_argument("--cfg", default="{}", help="JSON string or path")
    ap.add_argument("--name", required=True)
    ap.add_argument("--cv", default=None, help="all | id | id0 | lodo | id0+lodo")
    ap.add_argument("--eval", action="store_true", help="train on all night_train, predict every snapshot of --data")
    ap.add_argument("--train-data", default=None, help="(eval) training data dir if --data is a new batch")
    ap.add_argument("--control", default=None, choices=[None, "rewire", "shuffle_ef", "shuffle_labels"])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out-dir", default=os.path.join(HERE, "preds"))
    a = ap.parse_args()
    cfg = json.load(open(a.cfg)) if os.path.exists(a.cfg) else json.loads(a.cfg)
    if a.cv:
        t0 = time.time()
        P, cpu = run_cv(a.data, cfg, a.cv, a.workers, a.control, a.seed)
        os.makedirs(os.path.join(a.out_dir, "cv"), exist_ok=True)
        P.to_csv(os.path.join(a.out_dir, "cv", f"{a.name}.csv"), index=False)
        s = summarize(a.data, P) if a.cv in ("all", "id0+lodo", "lodo") else {}
        if a.cv in ("id", "id0"):
            from sklearn.metrics import roc_auc_score, average_precision_score
            S = pd.read_csv(os.path.join(a.data, "snapshots.csv"), low_memory=False)[["run", "round", "y3"]]
            Q = P.groupby(["run", "round"], as_index=False).score.mean().merge(S, on=["run", "round"])
            s = {"id_auroc": roc_auc_score(Q.y3, Q.score), "id_auprc": average_precision_score(Q.y3, Q.score)}
        s.update({"name": a.name, "cv": a.cv, "control": a.control, "wall_s": round(time.time() - t0), "cpu_s": round(cpu)})
        print(json.dumps(s))
        with open(os.path.join(a.out_dir, "cv_log.jsonl"), "a") as f:
            f.write(json.dumps({**s, "cfg": cfg}) + "\n")
    if a.eval:
        td = a.train_data or a.data
        c = {**DEFAULT, **cfg}
        Dtr = get_data(td, c["feat"], c["clock"])
        tr = [i for i, r in enumerate(Dtr.runs) if r["split"] == TRAIN_SPLIT]
        df, states, norm = fit_models(td, cfg, tr, a.seed, a.control, keep_states=True,
                                      pred_runs_idx=list(range(len(Dtr.runs))))
        os.makedirs(os.path.join(HERE, "models"), exist_ok=True)
        if a.control is None:
            torch.save({"cfg": {**DEFAULT, **cfg}, "states": states, "norm": norm},
                       os.path.join(HERE, "models", f"{a.name}.pt"))
        os.makedirs(os.path.join(a.out_dir, "eval"), exist_ok=True)
        df.to_csv(os.path.join(a.out_dir, "eval", f"{a.name}.csv"), index=False)
        print("wrote", os.path.join(a.out_dir, "eval", f"{a.name}.csv"), len(df))


if __name__ == "__main__":
    main()
