"""Compile and judge C++ the way an ICPC judge does.

    compile(source)                 -> Compiled (binary path or compiler errors)
    run(binary, stdin, time_limit)  -> Outcome  (stdout, CPU time, peak memory, exit status)
    judge(lesson, problem, code)    -> dict     (verdict per test, first failure, ...)

Verdicts use the contest vocabulary so it becomes familiar before a real contest:
AC accepted, WA wrong answer, TLE time limit exceeded, RE run-time error, OLE output
limit exceeded, CE compilation error.

The compiler is found once: $CPTUTOR_CXX if set, else the newest Homebrew/Linux GCC
(`g++-16`, `g++-15`, ...), else a `g++` that really is GCC, else clang++.  GCC is
what ICPC judges run and it ships <bits/stdc++.h>; for clang, harness/include has a
stand-in so the usual first line still compiles.

Limits.  CPU time is measured per test with wait4() and compared to the problem's
limit; a wall-clock timer kills runaways.  Output is capped (ulimit -f) and read from
a file, never a pipe, so `while (true) cout << 1;` cannot fill memory.  Memory is
reported, not enforced: macOS ignores RLIMIT_AS.  The main thread gets a 512 MB stack
(a linker flag on macOS, `ulimit -s unlimited` elsewhere) because contest judges allow
deep recursion and a 10^5-deep DFS should not segfault here when it would pass there.
"""
from __future__ import annotations

import glob
import hashlib
import math
import os
import random
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("CPTUTOR_DATA") or os.path.join(ROOT, "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
HARNESS_INCLUDE = os.path.join(ROOT, "harness", "include")

STD = "gnu++17"
OUTPUT_CAP = 32 << 20            # bytes a program may write before OLE
SHOWN = 4000                     # characters of input/output sent back per test
SHOW_HIDDEN_INPUT = 1500         # hidden tests up to this size show their input
BIN_KEEP = 600                   # compiled binaries kept in the cache
DARWIN = sys.platform == "darwin"

# Runs share the machine; too many at once and CPU time stops meaning anything.
RUN_SLOTS = threading.BoundedSemaphore(int(os.environ.get("CPTUTOR_RUN_SLOTS") or 0)
                                       or max(1, min(4, (os.cpu_count() or 2) // 2)))
COMPILE_SLOTS = threading.BoundedSemaphore(max(1, min(6, os.cpu_count() or 2)))


class JudgeError(Exception):
    """A problem with the curriculum or the machine, not with the learner's code."""


# -------------------------------------------------------------------- compiler
def _version(path: str) -> str:
    try:
        out = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except (OSError, subprocess.SubprocessError, IndexError):
        return ""


@lru_cache(maxsize=1)
def compiler() -> dict:
    """{"path", "version", "gcc": bool} for the compiler every compile uses."""
    forced = os.environ.get("CPTUTOR_CXX")
    if forced:
        path = shutil.which(forced) or forced
        v = _version(path)
        if not v:
            raise JudgeError(f"CPTUTOR_CXX={forced!r} does not run")
        return {"path": path, "version": v, "gcc": "clang" not in v.lower()}

    dirs = ["/opt/homebrew/bin", "/usr/local/bin"] + os.environ.get("PATH", "").split(os.pathsep)
    versioned = []
    for d in dict.fromkeys(dirs):
        for p in glob.glob(os.path.join(d, "g++-[0-9]*")):
            m = re.search(r"g\+\+-(\d+)$", p)
            if m and os.access(p, os.X_OK):
                versioned.append((int(m.group(1)), p))
    for _, p in sorted(versioned, reverse=True):
        v = _version(p)
        if v and "clang" not in v.lower():
            return {"path": p, "version": v, "gcc": True}
    for name in ("g++", "clang++", "c++"):
        p = shutil.which(name)
        if p:
            v = _version(p)
            if v:
                return {"path": p, "version": v, "gcc": "clang" not in v.lower()
                        and "apple" not in v.lower()}
    raise JudgeError("no C++ compiler found: install GCC (brew install gcc) "
                     "or set CPTUTOR_CXX=/path/to/g++")


def flags() -> list[str]:
    c = compiler()
    f = [f"-std={STD}", "-O2", "-pipe", "-Wall", "-Wno-sign-compare", "-Wno-unused-result",
         "-Wno-unused-const-variable", "-fdiagnostics-color=never",
         "-idirafter", HARNESS_INCLUDE]
    f.append("-fmax-errors=25" if c["gcc"] else "-ferror-limit=25")
    if DARWIN:
        f.append("-Wl,-stack_size,0x20000000")
    return f


@dataclass
class Compiled:
    ok: bool
    binary: str = ""
    errors: str = ""             # compiler output (errors, or warnings when ok)
    ms: float = 0.0
    cached: bool = False


def _prune(dirpath: str, keep: int) -> None:
    try:
        entries = [os.path.join(dirpath, n) for n in os.listdir(dirpath)]
    except OSError:
        return
    if len(entries) <= keep:
        return
    entries.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0)
    for p in entries[:len(entries) - keep + keep // 4]:
        try:
            os.unlink(p)
        except OSError:
            pass


def _tidy_errors(text: str, src_path: str) -> str:
    text = text.replace(src_path, "main.cpp")
    text = re.sub(r"^.*?main\.cpp", "main.cpp", text, flags=re.M)
    # linker noise nobody can act on
    lines = [ln for ln in text.splitlines() if "ld: warning" not in ln and "-stack_size" not in ln]
    return "\n".join(lines).strip()


def compile_source(source: str) -> Compiled:
    c = compiler()
    fl = flags()
    key = hashlib.sha1("\0".join([c["path"], c["version"], *fl, source]).encode()).hexdigest()
    bindir = os.path.join(CACHE_DIR, "bin")
    os.makedirs(bindir, exist_ok=True)
    binary = os.path.join(bindir, key)
    warn_path = binary + ".txt"
    if os.path.exists(binary):
        try:
            os.utime(binary)
        except OSError:
            pass
        warnings = ""
        if os.path.exists(warn_path):
            with open(warn_path, encoding="utf-8", errors="replace") as f:
                warnings = f.read()
        return Compiled(True, binary, warnings, 0.0, True)

    with COMPILE_SLOTS, tempfile.TemporaryDirectory(prefix="cc-", dir=CACHE_DIR) as tmp:
        src = os.path.join(tmp, "main.cpp")
        out = os.path.join(tmp, "a.out")
        with open(src, "w", encoding="utf-8") as f:
            f.write(source)
        t0 = time.monotonic()
        try:
            proc = subprocess.run([c["path"], *fl, src, "-o", out], capture_output=True,
                                  text=True, timeout=60, cwd=tmp)
        except subprocess.TimeoutExpired:
            return Compiled(False, errors="compiler took more than 60 s", ms=60000.0)
        ms = (time.monotonic() - t0) * 1000
        errors = _tidy_errors(proc.stderr or proc.stdout or "", src)
        if proc.returncode != 0 or not os.path.exists(out):
            return Compiled(False, errors=errors or "compilation failed", ms=ms)
        os.replace(out, binary)
        if errors:
            with open(warn_path, "w", encoding="utf-8") as f:
                f.write(errors)
    _prune(bindir, BIN_KEEP * 2)
    return Compiled(True, binary, errors, ms, False)


# ------------------------------------------------------------------------- run
SIGNALS = {
    signal.SIGSEGV: "segmentation fault: an out-of-bounds index, a null or dangling pointer, "
                    "or recursion deeper than the stack",
    signal.SIGBUS: "bus error: usually an out-of-bounds access, like a segfault",
    signal.SIGFPE: "floating-point exception: integer division or modulo by zero",
    signal.SIGABRT: "aborted: an assert failed, or an exception was thrown and not caught "
                    "(out_of_range from .at(), bad_alloc from a huge allocation, ...)",
    signal.SIGILL: "illegal instruction: often a function that should return a value fell "
                   "off its end without one",
    signal.SIGTRAP: "trap: undefined behaviour the compiler planted a trap for: a function "
                    "that should return a value reached its end without a `return`, or a "
                    "division by zero (ARM chips do not fault on it by themselves)",
    signal.SIGKILL: "killed",
    signal.SIGXCPU: "CPU time limit",
    signal.SIGXFSZ: "output limit: the program printed more than 32 MB",
}


@dataclass
class Outcome:
    status: str                  # ok | tle | re | ole
    stdout: str = ""
    stderr: str = ""
    cpu_ms: float = 0.0
    wall_ms: float = 0.0
    rss_kb: int = 0
    exit_code: int = 0
    message: str = ""            # human explanation for re / tle / ole


def run(binary: str, stdin: str, time_limit: float, wall_factor: float = 2.5) -> Outcome:
    """Run `binary` once with `stdin`, CPU-limited to `time_limit` seconds."""
    cpu_cap = max(1, math.ceil(time_limit) + 1)
    blocks = OUTPUT_CAP // 512
    stack = "" if DARWIN else "ulimit -s unlimited 2>/dev/null; "
    script = (f"ulimit -t {cpu_cap} 2>/dev/null; ulimit -f {blocks} 2>/dev/null; "
              f"ulimit -c 0 2>/dev/null; {stack}exec \"$0\"")
    os.makedirs(os.path.join(CACHE_DIR, "run"), exist_ok=True)
    with RUN_SLOTS, tempfile.TemporaryDirectory(prefix="run-", dir=os.path.join(CACHE_DIR, "run")) as tmp:
        pin, pout, perr = (os.path.join(tmp, n) for n in ("in", "out", "err"))
        with open(pin, "w", encoding="utf-8") as f:
            f.write(stdin)
        with open(pin, "rb") as fin, open(pout, "wb") as fout, open(perr, "wb") as ferr:
            t0 = time.monotonic()
            proc = subprocess.Popen(["/bin/sh", "-c", script, binary], stdin=fin, stdout=fout,
                                    stderr=ferr, cwd=tmp, close_fds=True)
            killed = threading.Event()
            done = threading.Event()

            def kill() -> None:
                if done.is_set():
                    return
                killed.set()
                try:
                    os.kill(proc.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass

            timer = threading.Timer(time_limit * wall_factor + 1.0, kill)
            timer.daemon = True
            timer.start()
            try:
                _, status, usage = os.wait4(proc.pid, 0)
            finally:
                done.set()
                timer.cancel()
            wall = (time.monotonic() - t0) * 1000
            proc.returncode = os.waitstatus_to_exitcode(status)
        out = _read(pout, OUTPUT_CAP)
        err = _read(perr, 64 << 10)

    cpu = (usage.ru_utime + usage.ru_stime) * 1000
    rss = int(usage.ru_maxrss / 1024) if DARWIN else int(usage.ru_maxrss)
    o = Outcome("ok", out, err, cpu, wall, rss, proc.returncode)
    sig = -proc.returncode if proc.returncode < 0 else 0
    if killed.is_set() or cpu > time_limit * 1000 or sig == signal.SIGXCPU:
        o.status = "tle"
        o.message = (f"used {cpu / 1000:.2f} s of CPU; the limit is {time_limit:g} s"
                     if not killed.is_set() else
                     f"still running after {wall / 1000:.1f} s of wall-clock time (waiting for input "
                     f"that never comes, or an infinite loop)")
    elif sig == signal.SIGXFSZ:
        o.status = "ole"
        o.message = SIGNALS[signal.SIGXFSZ]
    elif sig:
        o.status = "re"
        try:
            name = signal.Signals(sig).name
        except ValueError:
            name = f"signal {sig}"
        o.message = f"{name}: " + SIGNALS.get(sig, "killed by a signal").split(": ", 1)[-1]
    elif proc.returncode != 0:
        o.status = "re"
        o.message = (f"exit code {proc.returncode}: main() must return 0 "
                     f"(a non-zero return or exit() counts as a crash on ICPC judges)")
    return o


def _read(path: str, cap: int) -> str:
    try:
        with open(path, "rb") as f:
            return f.read(cap).decode("utf-8", errors="replace")
    except OSError:
        return ""


# --------------------------------------------------------------------- checkers
def _tokens(s: str) -> list[str]:
    return s.split()


def _locate(text: str, index: int) -> int:
    """1-based line of the index-th whitespace-separated token in `text`."""
    count = 0
    for ln, line in enumerate(text.splitlines(), 1):
        count += len(line.split())
        if count > index:
            return ln
    return max(1, len(text.splitlines()))


def _show(tok: str) -> str:
    return tok if len(tok) <= 40 else tok[:37] + "..."


def check(checker, inp: str, expected: str, got: str) -> tuple[bool, str]:
    """(accepted, message).  The message says where the first difference is."""
    if callable(checker):
        try:
            res = checker(inp, expected, got)
        except Exception as e:                                  # noqa: BLE001
            return False, f"your output could not be read: {type(e).__name__}: {e}"
        if isinstance(res, tuple):
            return bool(res[0]), str(res[1]) if len(res) > 1 else ""
        return bool(res), "" if res else "the output does not satisfy the problem"

    name, _, arg = str(checker).partition(":")
    if name == "lines":
        e = [ln.rstrip() for ln in expected.rstrip().splitlines()]
        g = [ln.rstrip() for ln in got.rstrip().splitlines()]
        for i, (a, b) in enumerate(zip(e, g), 1):
            if a != b:
                return False, f"line {i}: expected `{_show(a)}`, found `{_show(b)}`"
        if len(e) != len(g):
            return False, f"expected {len(e)} lines, found {len(g)}"
        return True, ""

    e, g = _tokens(expected), _tokens(got)
    eps = float(arg) if arg else 1e-6
    for i, (a, b) in enumerate(zip(e, g)):
        same = a == b
        if not same and name == "tokens_ci":
            same = a.lower() == b.lower()
        if not same and name == "float":
            try:
                fa, fb = float(a), float(b)
                same = math.isfinite(fb) and abs(fa - fb) <= eps * max(1.0, abs(fa))
            except ValueError:
                same = False
        if not same:
            hint = ""
            if name == "float":
                hint = f" (answers within {eps:g} are accepted)"
            elif a.lower() == b.lower():
                hint = " (case matters)"
            return False, (f"line {_locate(got, i)}: expected `{_show(a)}`, "
                           f"found `{_show(b)}`{hint}")
    if len(g) < len(e):
        return False, (f"output ended early: expected {len(e)} tokens, found {len(g)}; "
                       f"next expected `{_show(e[len(g)])}`")
    if len(g) > len(e):
        return False, f"extra output: expected {len(e)} tokens, found {len(g)}; first extra `{_show(g[len(e)])}`"
    return True, ""


# ------------------------------------------------------------------------ cases
@dataclass
class Case:
    name: str                    # "sample 1", "test 4", "random large #2"
    kind: str                    # sample | test | gen
    input: str
    output: Optional[str]        # None until the reference has produced it
    note: str = ""
    large: bool = False
    gen: str = ""
    brute: bool = True           # cross-checked against the problem's brute by the validator


_GEN_CACHE: dict[tuple, str] = {}
_GEN_LOCK = threading.Lock()


def seed_for(*parts) -> int:
    return int(hashlib.sha1("\0".join(map(str, parts)).encode()).hexdigest()[:15], 16)


def cases(lesson, problem, include_hidden: bool = True) -> list[Case]:
    out = [Case(f"sample {i}", "sample", t.input, t.output, t.note, brute=t.brute)
           for i, t in enumerate(problem.samples, 1)]
    if not include_hidden:
        return out
    n = len(out)
    for t in problem.tests:
        n += 1
        out.append(Case(f"test {n}", "test", t.input, t.output, t.note, brute=t.brute))
    for g in problem.gens:
        for k in range(g.count):
            n += 1
            key = (lesson.id, problem.id, g.name, k)
            with _GEN_LOCK:
                text = _GEN_CACHE.get(key)
            if text is None:
                text = g.fn(random.Random(seed_for(*key)))
                if not isinstance(text, str):
                    raise JudgeError(f"{lesson.id}.{problem.id}: generator {g.name!r} "
                                     f"returned {type(text).__name__}, not str")
                if not text.endswith("\n"):
                    text += "\n"
                with _GEN_LOCK:
                    _GEN_CACHE[key] = text
            out.append(Case(f"test {n}", "gen", text, None, "", g.large, g.name,
                            brute=(not g.large) if g.brute is None else g.brute))
    return out


def reference_output(problem, inp: str, label: str = "") -> str:
    """What the reference solution prints for `inp`, cached on disk by
    sha1(solution + input): the only two things that decide it."""
    key = hashlib.sha1((problem.solution + "\0" + inp).encode()).hexdigest()
    d = os.path.join(CACHE_DIR, "expected", key[:2])
    path = os.path.join(d, key)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    comp = compile_source(problem.solution)
    if not comp.ok:
        raise JudgeError(f"reference solution for {problem.id} does not compile:\n{comp.errors}")
    o = run(comp.binary, inp, max(5.0, problem.time_limit * 5))
    if o.status != "ok":
        raise JudgeError(f"reference solution for {problem.id} failed on {label or 'a test'}: "
                         f"{o.status} {o.message}")
    os.makedirs(d, exist_ok=True)
    tmp = path + f".{os.getpid()}.{threading.get_ident()}"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(o.stdout)
    os.replace(tmp, path)
    return o.stdout


def expected(problem, case: Case) -> str:
    if case.output is None:
        case.output = reference_output(problem, case.input, case.name)
    return case.output


# ------------------------------------------------------------------------ judge
def _clip(s: str, n: int = SHOWN) -> str:
    s = s or ""
    return s if len(s) <= n else s[:n] + f"\n... ({len(s) - n} more characters)"


VERDICT = {"ok": "AC", "tle": "TLE", "re": "RE", "ole": "OLE"}


def judge_binary(lesson, problem, binary: str, mode: str = "submit",
                 stop_on_fail: bool = True, reveal: bool = True) -> dict:
    """Run a compiled binary against the problem's tests.

    mode "samples": every sample, all shown.
    mode "submit":  samples then hidden tests; the first failure is the verdict, and
                    hidden tests stop there the way a contest judge stops.
    `reveal` shows small hidden inputs when they fail (the tutor is not a contest)."""
    all_cases = cases(lesson, problem, include_hidden=(mode == "submit"))
    results = []
    verdict, failed = "AC", ""
    max_ms, max_kb = 0.0, 0
    for c in all_cases:
        visible = c.kind == "sample"
        if verdict != "AC" and not visible and stop_on_fail:
            break
        o = run(binary, c.input, problem.time_limit)
        max_ms, max_kb = max(max_ms, o.cpu_ms), max(max_kb, o.rss_kb)
        row = {"name": c.name, "kind": c.kind, "gen": c.gen, "large": c.large,
               "ms": round(o.cpu_ms), "kb": o.rss_kb, "note": c.note}
        if o.status == "ok":
            want = expected(problem, c)
            ok, msg = check(problem.checker, c.input, want, o.stdout)
            row["verdict"] = "AC" if ok else "WA"
            row["message"] = msg
        else:
            want = c.output
            row["verdict"] = VERDICT[o.status]
            row["message"] = o.message
        show = visible or (reveal and len(c.input) <= SHOW_HIDDEN_INPUT)
        if row["verdict"] != "AC" or visible:
            row["input"] = _clip(c.input) if show else ""
            row["input_size"] = len(c.input)
            if want is None and show and row["verdict"] != "AC":
                try:
                    want = expected(problem, c)
                except JudgeError:
                    want = None
            row["expected"] = _clip(want) if (show and want is not None) else ""
            row["got"] = _clip(o.stdout) if show else _clip(o.stdout, 300)
            row["stderr"] = _clip(o.stderr, 1500)
        results.append(row)
        if row["verdict"] != "AC" and verdict == "AC":
            verdict, failed = row["verdict"], c.name
    total = len(all_cases)
    passed = sum(1 for r in results if r["verdict"] == "AC")
    return {"verdict": verdict, "failed": failed, "passed": passed, "total": total,
            "ran": len(results), "cases": results, "max_ms": round(max_ms), "max_kb": max_kb,
            "time_limit": problem.time_limit}


def judge(lesson, problem, code: str, mode: str = "submit") -> dict:
    comp = compile_source(code)
    if not comp.ok:
        return {"verdict": "CE", "compile": comp.errors, "cases": [], "passed": 0,
                "total": len(cases(lesson, problem, include_hidden=(mode == "submit"))),
                "ran": 0, "failed": "", "max_ms": 0, "max_kb": 0,
                "time_limit": problem.time_limit, "compile_ms": round(comp.ms)}
    res = judge_binary(lesson, problem, comp.binary, mode)
    res["warnings"] = comp.errors
    res["compile_ms"] = round(comp.ms)
    return res


def run_custom(problem, code: str, stdin: str) -> dict:
    """Your program on your input, next to what the reference prints for it."""
    comp = compile_source(code)
    if not comp.ok:
        return {"verdict": "CE", "compile": comp.errors}
    o = run(comp.binary, stdin, problem.time_limit if problem else 2.0)
    res = {"verdict": VERDICT[o.status], "stdout": _clip(o.stdout), "stderr": _clip(o.stderr, 3000),
           "ms": round(o.cpu_ms), "kb": o.rss_kb, "message": o.message, "warnings": comp.errors}
    if problem is not None:
        try:
            ref = reference_output(problem, stdin, "your input")
            res["reference"] = _clip(ref)
            if o.status == "ok":
                res["matches"] = check(problem.checker, stdin, ref, o.stdout)[0]
        except JudgeError as e:
            res["reference_error"] = str(e).split(": ", 1)[-1]
    return res
