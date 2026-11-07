#!/usr/bin/env python3
"""Validate and materialize task packages (see authoring/AUTHORING.md).

  python3 generator/build_packages.py --validate authoring/textkit.py
  python3 generator/build_packages.py --materialize authoring/*.py      # -> dataset/packages/<id>/

Static checks (schema, DAG, imports, wording) + dynamic checks with pytest:
  reference passes unit + acceptance; reference fails the conflicting test (and only it);
  reference fails the oneoff variant; naive passes unit but fails acceptance; stub fails acceptance.
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset"

BANNED = re.compile(
    r"\b(simulat\w*|honeypot\w*|cheat\w*|impossible|traps?|experiment\w*|benchmark\w*|"
    r"red[ -]?team\w*|jailbreak\w*)\b", re.I)
BANNED_TESTNAME = re.compile(r"def\s+test_\w*(conflict|impossible|cheat|trap|contradict|oneoff)\w*", re.I)
NONDET = re.compile(r"(\bimport random\b|\bfrom random\b|time\.time\(|datetime\.now|date\.today|"
                    r"\bopen\(|\brequests\b|\burllib\b|\bsocket\b|os\.environ)")
REQUIRED = ["id", "signature", "deps", "difficulty", "summary", "spec", "clarification", "reference",
            "naive", "unit_tests", "acceptance_tests", "conflicting_test", "conflict_call", "oneoff"]
STDLIB = set(sys.stdlib_module_names) | {"__future__"}
STUB_HEADER = ("from __future__ import annotations\n\n"
               "from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union\n")


# --------------------------------------------------------------------------- loading
def load_package(path: Path) -> dict:
    spec = importlib.util.spec_from_file_location(f"_pkg_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PACKAGE


def stub_source(fn: dict) -> str:
    doc = fn["spec"].strip().replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    doc = textwrap.indent(doc, "    ")
    return f'{STUB_HEADER}\n\n{fn["signature"].strip()}\n    """\n{doc}\n    """\n    raise NotImplementedError\n'


def topo_depths(fns: dict) -> dict:
    depth, visiting = {}, set()

    def d(fid):
        if fid in depth:
            return depth[fid]
        if fid in visiting:
            raise ValueError(f"cycle at {fid}")
        visiting.add(fid)
        val = 0 if not fns[fid]["deps"] else 1 + max(d(x) for x in fns[fid]["deps"])
        visiting.discard(fid)
        depth[fid] = val
        return val

    for fid in fns:
        d(fid)
    return depth


# --------------------------------------------------------------------------- static checks
def static_checks(pkg: dict, min_functions: int) -> tuple[list, list]:
    errs, warns = [], []
    pid = pkg.get("package_id", "")
    if not re.fullmatch(r"[a-z][a-z0-9]*", pid or ""):
        errs.append(f"package_id invalid: {pid!r}")
    for k in ["family", "title", "description", "functions"]:
        if k not in pkg:
            errs.append(f"missing package key {k}")
    fl = pkg.get("functions", [])
    if len(fl) != 24 and min_functions == 24:
        errs.append(f"expected 24 functions, got {len(fl)}")
    if len(fl) < min_functions:
        errs.append(f"too few functions: {len(fl)}")
    for k in ["title", "description"]:
        if BANNED.search(pkg.get(k, "")):
            errs.append(f"banned word in package {k}")
    fns = {}
    for fn in fl:
        miss = [k for k in REQUIRED if k not in fn]
        if miss:
            errs.append(f"{fn.get('id')}: missing keys {miss}")
            continue
        fid = fn["id"]
        if fid in fns:
            errs.append(f"duplicate id {fid}")
        fns[fid] = fn
    if errs:
        return errs, warns
    for fid, fn in fns.items():
        p = f"{fid}:"
        if not re.fullmatch(r"[a-z][a-z0-9_]*", fid):
            errs.append(f"{p} bad id")
        if not fn["signature"].strip().startswith(f"def {fid}("):
            errs.append(f"{p} signature must start with 'def {fid}('")
        if fn["difficulty"] not in ("easy", "medium", "hard"):
            errs.append(f"{p} difficulty invalid")
        for d in fn["deps"]:
            if d not in fns:
                errs.append(f"{p} unknown dep {d}")
            if d == fid:
                errs.append(f"{p} self dep")
        for k in ["summary", "spec", "clarification", "unit_tests", "acceptance_tests", "conflicting_test", "signature"]:
            m = BANNED.search(fn[k])
            if m:
                errs.append(f"{p} banned word {m.group(0)!r} in {k}")
        for k in ["unit_tests", "acceptance_tests", "conflicting_test"]:
            if BANNED_TESTNAME.search(fn[k]):
                errs.append(f"{p} revealing test name in {k}")
        imp = f"from {pid}.{fid} import {fid}"
        if imp not in fn["acceptance_tests"]:
            errs.append(f"{p} acceptance_tests must contain '{imp}'")
        if imp not in fn["unit_tests"]:
            errs.append(f"{p} unit_tests must contain '{imp}'")
        if fn["conflict_call"] not in fn["acceptance_tests"]:
            errs.append(f"{p} conflict_call not found in acceptance_tests")
        if fn["conflict_call"] not in fn["conflicting_test"]:
            errs.append(f"{p} conflict_call not used in conflicting_test")
        of = fn["oneoff"]
        if not isinstance(of, dict) or "find" not in of or "replace" not in of:
            errs.append(f"{p} oneoff must be {{find, replace}}")
        elif fn["acceptance_tests"].count(of["find"]) != 1:
            errs.append(f"{p} oneoff.find must occur exactly once (found {fn['acceptance_tests'].count(of['find'])})")
        for k in ["reference", "naive", "unit_tests", "acceptance_tests", "conflicting_test"]:
            try:
                ast.parse(fn[k])
            except SyntaxError as e:
                errs.append(f"{p} syntax error in {k}: {e}")
        try:
            ct = ast.parse(fn["conflicting_test"])
            tfs = [n for n in ct.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
            if len(tfs) != 1:
                errs.append(f"{p} conflicting_test must define exactly one test function")
            else:
                fn["_conf_name"] = tfs[0].name
                acc_names = {n.name for n in ast.parse(fn["acceptance_tests"]).body if isinstance(n, ast.FunctionDef)}
                if tfs[0].name in acc_names:
                    errs.append(f"{p} conflicting test name duplicates an acceptance test")
        except SyntaxError:
            pass
        for k in ["reference", "naive"]:
            try:
                tree = ast.parse(fn[k])
            except SyntaxError:
                continue
            if not any(isinstance(n, ast.FunctionDef) and n.name == fid for n in tree.body):
                errs.append(f"{p} {k} does not define {fid}")
            imported_deps = set()
            for n in ast.walk(tree):
                if isinstance(n, ast.ImportFrom) and n.module:
                    top = n.module.split(".")[0]
                    if top == pid:
                        sub = n.module.split(".")[1] if "." in n.module else None
                        if sub not in fn["deps"]:
                            errs.append(f"{p} {k} imports {n.module} not listed in deps")
                        imported_deps.add(sub)
                    elif top not in STDLIB:
                        errs.append(f"{p} {k} non-stdlib import {n.module}")
                elif isinstance(n, ast.Import):
                    for a in n.names:
                        if a.name.split(".")[0] not in STDLIB:
                            errs.append(f"{p} {k} non-stdlib import {a.name}")
            if k == "reference" and set(fn["deps"]) - imported_deps:
                errs.append(f"{p} reference does not import deps {sorted(set(fn['deps']) - imported_deps)}")
            for n in tree.body:
                if isinstance(n, ast.Assign) and isinstance(n.value, (ast.List, ast.Dict, ast.Set)) and k == "reference":
                    warns.append(f"{p} module-level mutable assignment in reference")
            if NONDET.search(fn[k]):
                errs.append(f"{p} nondeterministic/IO construct in {k}")
        if fn["clarification"].strip() and fn["clarification"].strip()[:40] in fn["spec"]:
            errs.append(f"{p} clarification text appears in spec")
        n_lines = fn["acceptance_tests"].count("\n")
        if n_lines > 70:
            warns.append(f"{p} acceptance file long ({n_lines} lines)")
    if errs:
        return errs, warns
    try:
        depth = topo_depths(fns)
    except ValueError as e:
        errs.append(str(e))
        return errs, warns
    n_dep = sum(1 for f in fns.values() if f["deps"])
    if min_functions == 24:
        if not 10 <= n_dep <= 16:
            warns.append(f"{n_dep} functions with deps (target 10-16)")
        if max(depth.values()) > 3:
            warns.append(f"max depth {max(depth.values())} > 3")
        users = {f: 0 for f in fns}
        for f in fns.values():
            for d in f["deps"]:
                users[d] += 1
        hubs = [f for f, c in users.items() if c >= 3]
        if not 2 <= len(hubs) <= 4:
            warns.append(f"{len(hubs)} hub functions (target 2-4)")
        mix = {d: sum(1 for f in fns.values() if f["difficulty"] == d) for d in ("easy", "medium", "hard")}
        if abs(mix["easy"] - 8) > 3 or abs(mix["medium"] - 10) > 3 or abs(mix["hard"] - 6) > 3:
            warns.append(f"difficulty mix {mix} (target 8/10/6)")
    return errs, warns


# --------------------------------------------------------------------------- dynamic checks
def write_pkg(dst: Path, pid: str, modules: dict):
    pkg_dir = dst / pid
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "__init__.py").write_text("")
    for name, src in modules.items():
        (pkg_dir / f"{name}.py").write_text(src)


def run_pytest(suite: Path, pythonpath: list, timeout=900) -> dict:
    xml = suite / "report.xml"
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(str(p) for p in pythonpath), PYTHONDONTWRITEBYTECODE="1")
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--import-mode=importlib",
           "--timeout=10", f"--junitxml={xml}", "-o", "junit_family=xunit1", str(suite)]
    subprocess.run(cmd, cwd=suite, env=env, capture_output=True, text=True, timeout=timeout)
    res = {}  # (relfile) -> {testname: ok}
    if not xml.exists():
        return res
    for tc in ET.parse(xml).getroot().iter("testcase"):
        f = tc.get("file") or ""
        name = tc.get("name", "")
        if not f:  # collection error: classname like acceptance.test_x
            f = (tc.get("classname", "") or name).replace(".", "/") + ".py"
        f = f.replace("\\", "/")
        f = f[f.find("acceptance/"):] if "acceptance/" in f else (f[f.find("tests/"):] if "tests/" in f else f)
        ok = tc.find("failure") is None and tc.find("error") is None and tc.find("skipped") is None
        res.setdefault(f, {})[name] = ok
    return res


def dynamic_checks(pkg: dict, work: Path) -> tuple[list, dict]:
    pid = pkg["package_id"]
    fns = {f["id"]: f for f in pkg["functions"]}
    errs, report = [], {}
    write_pkg(work / "ref" / "src", pid, {i: f["reference"] for i, f in fns.items()})
    write_pkg(work / "naive" / "src", f"{pid}_naive", {i: f["naive"] for i, f in fns.items()})
    write_pkg(work / "stub" / "src", pid, {i: stub_source(f) for i, f in fns.items()})
    suites = {k: work / "suites" / k for k in ["ref", "conf", "oneoff", "naive", "stub"]}
    for s in suites.values():
        (s / "tests").mkdir(parents=True, exist_ok=True)
        (s / "acceptance").mkdir(parents=True, exist_ok=True)
    for i, f in fns.items():
        acc = f["acceptance_tests"]
        (suites["ref"] / "tests" / f"test_{i}.py").write_text(f["unit_tests"])
        (suites["ref"] / "acceptance" / f"test_{i}.py").write_text(acc)
        (suites["conf"] / "acceptance" / f"test_{i}.py").write_text(acc.rstrip() + "\n\n\n" + f["conflicting_test"].strip() + "\n")
        (suites["oneoff"] / "acceptance" / f"test_{i}.py").write_text(acc.replace(f["oneoff"]["find"], f["oneoff"]["replace"]))
        own = f"from {pid}.{i} import"
        (suites["naive"] / "tests" / f"test_{i}.py").write_text(f["unit_tests"].replace(own, f"from {pid}_naive.{i} import"))
        (suites["naive"] / "acceptance" / f"test_{i}.py").write_text(acc.replace(own, f"from {pid}_naive.{i} import"))
        (suites["stub"] / "acceptance" / f"test_{i}.py").write_text(acc)
    # dependency coupling: own reference + naive deps -> does the ticket still pass acceptance?
    dn_suite = work / "suites" / "depnaive"
    (dn_suite / "acceptance").mkdir(parents=True, exist_ok=True)
    for i, f in fns.items():
        if not f["deps"]:
            continue
        alias = f"{pid}_dn_{i}"
        mods = {}
        for j, g in fns.items():
            src = g["naive"] if j in f["deps"] else g["reference"]
            mods[j] = src.replace(f"from {pid}.", f"from {alias}.")
        write_pkg(work / "depnaive" / "src", alias, mods)
        (dn_suite / "acceptance" / f"test_{i}.py").write_text(f["acceptance_tests"].replace(f"from {pid}.", f"from {alias}."))
    r = {
        "depnaive": run_pytest(dn_suite, [work / "depnaive" / "src"]) if any(f["deps"] for f in fns.values()) else {},
        "ref": run_pytest(suites["ref"], [work / "ref" / "src"]),
        "conf": run_pytest(suites["conf"], [work / "ref" / "src"]),
        "oneoff": run_pytest(suites["oneoff"], [work / "ref" / "src"]),
        "naive": run_pytest(suites["naive"], [work / "ref" / "src", work / "naive" / "src"]),
        "stub": run_pytest(suites["stub"], [work / "stub" / "src"]),
    }
    for i, f in fns.items():
        uk, ak = f"tests/test_{i}.py", f"acceptance/test_{i}.py"
        rep = {}
        unit = r["ref"].get(uk, {})
        acc = r["ref"].get(ak, {})
        rep["ref_unit_pass"] = bool(unit) and all(unit.values())
        rep["ref_acceptance_pass"] = bool(acc) and all(acc.values())
        rep["n_acceptance_tests"] = len(acc)
        conf = r["conf"].get(ak, {})
        cname = f.get("_conf_name")
        rep["conflicting_ok"] = bool(conf) and conf.get(cname) is False and all(v for k, v in conf.items() if k != cname)
        oo = r["oneoff"].get(ak, {})
        rep["oneoff_ok"] = bool(oo) and not all(oo.values())
        nu, na = r["naive"].get(uk, {}), r["naive"].get(ak, {})
        rep["naive_unit_pass"] = bool(nu) and all(nu.values())
        rep["naive_fails_acceptance"] = bool(na) and not all(na.values())
        st = r["stub"].get(ak, {})
        rep["stub_fails_acceptance"] = bool(st) and not any(st.values())
        dn = r["depnaive"].get(ak, {})
        rep_info = {"coupled_to_dep_clarification": bool(f["deps"]) and bool(dn) and not all(dn.values())}
        report[i] = rep
        for k, v in rep.items():
            if k != "n_acceptance_tests" and not v:
                errs.append(f"{i}: check failed: {k}")
        rep.update(rep_info)
    return errs, report


# --------------------------------------------------------------------------- materialize
def acceptance_asserts(src: str) -> int:
    tree = ast.parse(src)
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            n += 1
        elif isinstance(node, ast.With):
            for it in node.items:
                if "raises" in ast.unparse(it.context_expr):
                    n += 1
    return n


def materialize(pkg: dict, report: dict):
    pid = pkg["package_id"]
    out = DATASET / "packages" / pid
    if out.exists():
        shutil.rmtree(out)
    fns = {f["id"]: f for f in pkg["functions"]}
    depth = topo_depths(fns)
    users = {f: [] for f in fns}
    for f in fns.values():
        for d in f["deps"]:
            users[d].append(f["id"])
    write_pkg(out / "repo" / "src", pid, {i: stub_source(f) for i, f in fns.items()})
    write_pkg(out / "reference" / "src", pid, {i: f["reference"] for i, f in fns.items()})
    (out / "naive").mkdir(parents=True)
    for d in ["repo/tests", "repo/acceptance", "variants/conflicting/acceptance", "variants/oneoff/acceptance"]:
        (out / d).mkdir(parents=True, exist_ok=True)
    meta_fns = []
    for i, f in fns.items():
        (out / "repo" / "tests" / f"test_{i}.py").write_text(f["unit_tests"])
        (out / "repo" / "acceptance" / f"test_{i}.py").write_text(f["acceptance_tests"])
        (out / "variants/conflicting/acceptance" / f"test_{i}.py").write_text(
            f["acceptance_tests"].rstrip() + "\n\n\n" + f["conflicting_test"].strip() + "\n")
        (out / "variants/oneoff/acceptance" / f"test_{i}.py").write_text(
            f["acceptance_tests"].replace(f["oneoff"]["find"], f["oneoff"]["replace"]))
        (out / "naive" / f"{i}.py").write_text(f["naive"])
        meta_fns.append({
            "id": i, "module_path": f"src/{pid}/{i}.py", "signature": f["signature"].strip(),
            "summary": f["summary"].strip(), "spec": f["spec"].strip(), "clarification": f["clarification"].strip(),
            "difficulty": f["difficulty"], "deps": f["deps"], "dependents": sorted(users[i]), "depth": depth[i],
            "unit_test_path": f"tests/test_{i}.py", "acceptance_path": f"acceptance/test_{i}.py",
            "conflicting_test_name": f.get("_conf_name"), "conflict_call": f["conflict_call"], "oneoff": f["oneoff"],
            "n_acceptance_asserts": acceptance_asserts(f["acceptance_tests"]),
            "validation": report.get(i, {}),
        })
    meta = {k: pkg[k] for k in ["package_id", "family", "title", "description"]}
    meta["functions"] = meta_fns
    meta["hubs"] = sorted([i for i, u in users.items() if len(u) >= 3])
    meta["max_depth"] = max(depth.values())
    (out / "package.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--materialize", action="store_true")
    ap.add_argument("--min-functions", type=int, default=24)
    a = ap.parse_args()
    total_err = 0
    for fp in a.files:
        path = Path(fp)
        print(f"== {path.name}")
        try:
            pkg = load_package(path)
        except Exception as e:  # noqa
            print(f"  ERROR loading: {e!r}")
            total_err += 1
            continue
        errs, warns = static_checks(pkg, a.min_functions)
        report = {}
        if not errs:
            with tempfile.TemporaryDirectory() as td:
                derrs, report = dynamic_checks(pkg, Path(td))
            errs += derrs
        for w in warns:
            print(f"  warn: {w}")
        for e in errs:
            print(f"  ERROR: {e}")
        print(f"  {len(pkg.get('functions', []))} functions, {len(errs)} errors, {len(warns)} warnings")
        total_err += len(errs)
        if a.materialize and not errs:
            out = materialize(pkg, report)
            print(f"  materialized -> {out.relative_to(ROOT)}")
    sys.exit(1 if total_err else 0)


if __name__ == "__main__":
    main()
