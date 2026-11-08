"""Parity tests: the monitors see exactly the GNN's messages, nothing hidden, no clock, nothing from the future.

  .venv/bin/python -m pytest llm_monitor/tests -q
"""
from __future__ import annotations

import os
import re
import shutil

import pytest

from llm_monitor import common as C
from llm_monitor.units import build_calls

RUNS = C.find_runs(os.path.join(C.REPO, "sim_dataset", "runs_night"))
SAMPLE = [r for r in RUNS if r.endswith(("core-night_branch-K2-001/rep0-fake_authority",
                                         "core-night_train-K4-010/rep1", "core-night_train-K2-034/rep0"))]
VARIANTS = ["global_full", "global_window", "pairwise", "agent", "global_sequential", "global_full_informed"]
TAG = re.compile(r"<msg [^>]*>.*?</msg>", re.S)


def gnn_message_ids(run_dir, tmp):
    """Message ids that runner/features.py build_features actually uses (recorded from its edge typing call)."""
    import features
    for f in ("messages.jsonl", "jury_merged.jsonl", "events.jsonl"):
        shutil.copy(os.path.join(run_dir, f), tmp)
    seen = set()
    orig = features.message_edges_typed

    def rec(m):
        seen.add(m["id"])
        return orig(m)

    features.message_edges_typed = rec
    try:
        features.build_features(C.scenario(C.scenario_id(run_dir)), tmp, nli=None)
    finally:
        features.message_edges_typed = orig
    return seen


@pytest.mark.parametrize("run_dir", SAMPLE)
def test_message_set_equals_features(run_dir, tmp_path):
    assert len(SAMPLE) == 3
    want = gnn_message_ids(run_dir, tmp_path)
    got = {m["id"] for m in C.load_messages(run_dir)}
    assert got == want
    last = build_calls(run_dir, "global_full")[-1]
    assert set(last["ids"]) == want
    assert last["blocks"][0].count("<msg ") == len(want)


@pytest.mark.parametrize("run_dir", SAMPLE)
@pytest.mark.parametrize("variant", VARIANTS)
def test_no_hidden_kinds_no_clock_no_future(run_dir, variant):
    ms = C.read_jsonl(C._p(run_dir, "messages.jsonl"))
    hidden = {m["id"] for m in ms if m.get("kind") in ("notice", "review_request")}
    visible_texts = {str(m["text"]).strip() for m in ms if C.gnn_visible(m)}
    hidden_texts = {str(m["text"]).strip() for m in ms if m["id"] in hidden} - visible_texts
    rnd = {m["id"]: m["round"] for m in ms}
    models = {a["model"] for a in C.scenario(C.scenario_id(run_dir))["population"]}
    R = C.n_rounds(run_dir)
    for cl in build_calls(run_dir, variant, k=1):
        t = cl["t"]
        assert not (set(cl["ids"]) & hidden)
        assert all(rnd[i] <= t for i in cl["ids"]), "message from after t"
        if variant in ("global_window", "pairwise", "agent"):
            assert all(rnd[i] >= t - C.WINDOW for i in cl["ids"])
        text = "\n".join(cl["blocks"]) if cl["blocks"] else cl["round_block"]
        assert not re.search(r'id="m\d+', text)
        for h in hidden_texts:
            if len(h) > 20:
                assert h not in text, "hidden (notice / review_request) text rendered"
        markup = TAG.sub("<msg/>", text)          # renderer output without message contents
        for rel in re.findall(r'rel="(-?\d+)"', markup):
            assert int(rel) <= 0
        assert not re.search(r"round=\"\d|round \d|\bR\s*=\s*\d|sprint length|deadline", markup, re.I)
        assert str(R) + " rounds" not in markup
        for mod in models:
            assert mod not in markup and mod.split("-")[0] not in markup.lower()
        for msg in re.findall(r"<msg [^>]*>", text):
            assert not re.search(r'\bround="?\d', msg)


def test_notices_only_in_notice_variant():
    run_dir = SAMPLE[0]
    ms = C.read_jsonl(C._p(run_dir, "messages.jsonl"))
    notice_ids = {m["id"] for m in ms if m.get("kind") == "notice"}
    ids = set(build_calls(run_dir, "global_full_notices")[-1]["ids"])
    assert notice_ids <= ids
    assert not ({m["id"] for m in ms if m.get("kind") == "review_request"} & ids)
