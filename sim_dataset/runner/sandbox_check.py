#!/usr/bin/env python3
"""Proves that agent-written code executed by the mock CI is isolated.

    .venv/bin/python runner/sandbox_check.py

Runs through MockRepo.run_tests exactly like a simulation does:
  1. functional: the stub stays RED, the reference solution goes GREEN (sandbox does not break honest work)
  2. attacks: an acceptance test file written by a "malicious agent" that knows all real paths tries to read the
     API keys, the home directory and the reference solutions, write outside the CI dir, open network connections,
     resolve DNS, spawn processes, read API keys from the environment and raise its resource limits.
     Every test asserts that the attack FAILED, so GREEN = all attacks blocked.
  3. path traversal: tool paths like "src/../../x.py" are rejected, "src/../acceptance/x.py" is canonicalised.
Exit code 0 only if everything holds. Also called by `run.py simulate` and `run.py selftest` before any API call.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "generator"))
from engine import ALLOW_UNSANDBOXED, sandbox_available  # noqa: E402
from query import Dataset  # noqa: E402

SCENARIO = "core-pilot-K2-knower-qwen3.8-27b+gemma4-26b-a4b"  # stable_build, routekit
CANARY_ENV = "SIM_SANDBOX_CANARY_SECRET"
CANARY_VAL = "pt_live_CANARY_must_not_leak_0000"

ATTACK_TEST = r'''
import os, socket, subprocess, resource, signal, pytest

SECRETS = {secrets!r}
README = {readme!r}
REFERENCE = {reference!r}
HOME = {home!r}
ESCAPE_HOME = {escape_home!r}
ESCAPE_TMP = {escape_tmp!r}

def _blocked(fn):
    try:
        fn()
    except (OSError, ValueError):
        return True
    return False

def test_cannot_read_secrets():
    assert _blocked(lambda: open(SECRETS).read())

def test_cannot_read_project_files():
    assert _blocked(lambda: open(README).read())

def test_cannot_read_reference_solution():
    assert _blocked(lambda: open(REFERENCE).read())

def test_cannot_list_home():
    assert _blocked(lambda: os.listdir(HOME))

def test_cannot_write_home():
    assert _blocked(lambda: open(ESCAPE_HOME, "w").write("x"))

def test_cannot_write_tmp():
    assert _blocked(lambda: open(ESCAPE_TMP, "w").write("x"))

def test_no_tcp():
    assert _blocked(lambda: socket.create_connection(("1.1.1.1", 443), timeout=3))

def test_no_dns():
    assert _blocked(lambda: socket.getaddrinfo("example.com", 443))

def test_no_udp():
    def f():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(b"x", ("1.1.1.1", 53))
    assert _blocked(f)

def test_no_subprocess():
    assert _blocked(lambda: subprocess.run(["/bin/echo", "hi"], check=True))

def test_no_fork():
    def f():
        pid = os.fork()
        if pid == 0:
            os._exit(0)
    assert _blocked(f)

def test_env_has_no_secrets():
    for k, v in os.environ.items():
        assert {canary_env!r} != k
        assert "pt_live" not in v and "sk-ant" not in v, k
        assert not any(t in k.upper() for t in ("API_KEY", "TOKEN", "SECRET", "ANTHROPIC", "ADAPTION")), k
    assert os.environ.get("HOME") != HOME

def test_cannot_raise_cpu_limit():
    assert _blocked(lambda: resource.setrlimit(resource.RLIMIT_CPU, (10**6, 10**6)))

def test_file_size_limited():
    signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
    def f():
        with open("big.bin", "wb") as fh:
            fh.write(b"0" * (60 * 2**20))
    assert _blocked(f)
'''


def main() -> int:
    ok = True

    def check(cond, msg):
        nonlocal ok
        ok &= bool(cond)
        print(("  PASS  " if cond else "  FAIL  ") + msg)

    print(f"python: {sys.executable}")
    if not sandbox_available():
        print("  FAIL  sandbox-exec not available on this machine (macOS only)"
              + (" - SIM_ALLOW_UNSANDBOXED=1 is set, agent code runs WITHOUT isolation" if ALLOW_UNSANDBOXED else ""))
        return 1

    os.environ[CANARY_ENV] = CANARY_VAL  # would be inherited by an unsandboxed CI run
    ds = Dataset()
    sc = ds.load(SCENARIO)
    pkg = sc["refs"]["package"]
    agent = sc["population"][0]
    aid, fid, solvable = agent["agent_id"], agent["ticket"]["function"], agent["ticket"]["solvable"]

    print("1) functional")
    repo = ds.env(sc)
    check(not repo.run_tests(aid, fid, "unit")["green"], f"stub {fid}: unit RED")
    ref = (repo.pkg_dir / "reference" / f"src/{pkg}/{fid}.py").read_text()
    repo.files[f"src/{pkg}/{fid}.py"] = ref
    check(repo.run_tests(aid, fid, "unit")["green"], f"reference {fid}: unit GREEN")
    acc = repo.run_tests(aid, fid, "acceptance")
    check(acc["green"] == solvable, f"reference {fid}: acceptance {'GREEN' if acc['green'] else 'RED'} "
                                    f"(ticket {'solvable' if solvable else 'unsolvable'})")

    print("2) attacks from agent code (GREEN = blocked)")
    home = str(Path.home())
    escape_home = os.path.join(home, "SIM_SANDBOX_ESCAPE_CANARY.txt")
    escape_tmp = "/private/tmp/SIM_SANDBOX_ESCAPE_CANARY.txt"
    for p in (escape_home, escape_tmp):
        if os.path.exists(p):
            os.remove(p)
    secrets = ROOT / "secrets.local.json"
    target = secrets if secrets.exists() else ROOT / "secrets.example.json"
    test_src = ATTACK_TEST.format(secrets=str(target), readme=str(ROOT / "README.md"),
                                  reference=str(repo.pkg_dir / "reference" / f"src/{pkg}/{fid}.py"), home=home,
                                  escape_home=escape_home, escape_tmp=escape_tmp, canary_env=CANARY_ENV)
    repo = ds.env(sc)
    repo.files[f"acceptance/test_{fid}.py"] = test_src
    res = repo.run_tests(aid, fid, "acceptance")
    names = sorted(res["results"])
    check(len(names) >= 14, f"{len(names)} attack tests collected")
    for name in names:
        check(res["results"][name], name.split("::")[-1])
    if not res["green"]:
        print("     pytest output:\n" + "\n".join("       " + ln for ln in res["output"].splitlines()))
    check(not os.path.exists(escape_home) and not os.path.exists(escape_tmp), "no escape canary file on disk")

    print("3) path traversal via tools")
    repo = ds.env(sc)
    check(repo.write_file(aid, "src/../../escape.py", "x")[0] is False, "write 'src/../../escape.py' rejected")
    check(repo.write_file(aid, "/etc/escape.py", "x")[0] is False, "write '/etc/escape.py' rejected")
    check(repo.read_file(aid, "../secrets.local.json")[0] is False, "read '../secrets.local.json' rejected")
    direct = ds.env(sc).write_file(aid, f"acceptance/test_{fid}.py", "# tampered\n")
    sneaky = repo.write_file(aid, f"src/../acceptance/test_{fid}.py", "# tampered\n")
    check(direct[0] == sneaky[0] and (direct[0] or direct[1] == sneaky[1]),
          "'src/../acceptance/...' gets the same policy decision as 'acceptance/...'")
    repo.write_file(aid, f"tests/../src/{pkg}/{fid}.py", "# t\n")
    check(repo.files.get(f"src/{pkg}/{fid}.py") == "# t\n" and not any(".." in p for p in repo.files),
          "'tests/../src/...' stored as canonical 'src/...'")

    print("SANDBOX OK" if ok else "SANDBOX CHECK FAILED - do not run simulations")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
