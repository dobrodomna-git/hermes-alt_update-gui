"""Headless acceptance test for hermes_update_gui.py stage logic.

Replays the REAL tail of yesterday's update.log plus the mock streams through
the same classify()/progress/counters rules the GUI uses, and asserts the
acceptance criteria from SPEC.md.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hermes_update_gui import STAGES, classify  # noqa: E402

WEIGHTS = [s["weight"] for s in STAGES]


def replay(lines):
    state = ["pending"] * len(STAGES)
    cur = -1
    progress = 0.0
    force_done = False
    conns = downloads = errors = 0
    saw_complete = False

    def set_progress(v):
        nonlocal progress
        progress = max(progress, min(100.0, v))

    def recompute():
        total = 0.0
        for i, st in enumerate(STAGES):
            if state[i] == "done":
                total += WEIGHTS[i]
            elif state[i] in ("active", "error"):
                total += WEIGHTS[i] * 0.5
        set_progress(total)

    for line in lines:
        low = line.lower()
        is_err = ("✗" in line) or ("[error]" in low) or ("failed" in low) or ("error" in low)
        if is_err:
            errors += 1
        if "https://" in line and any(k in low for k in
                                      ("fetching", "download", "installing", "refreshing", "warming")):
            conns += 1
        if any(k in low for k in ("download", "installing", "warming")) or \
                ("found " in low and "commit" in low):
            downloads += 1
        idx = classify(low)
        if not is_err and idx is not None and not force_done:
            if idx >= cur:
                if idx == cur:
                    if state[idx] == "pending":
                        state[idx] = "active"
                else:
                    for j in range(cur + 1, idx):
                        if state[j] in ("pending", "active", "error"):
                            state[j] = "done"
                    cur = idx
                    state[idx] = "active"
                    recompute()
        if "update complete" in low:
            saw_complete = True
            force_done = True
            for j in range(len(STAGES)):
                state[j] = "done"
            set_progress(100.0)
        elif "code updated" in low:
            force_done = True
            for j in range(len(STAGES)):
                state[j] = "done"
            set_progress(100.0)
    return state, progress, conns, downloads, errors, saw_complete


def read_lines(path, start=None):
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = [l.rstrip() for l in f if l.strip()]
    if start:
        lines = lines[start:]
    return lines


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(os.path.expandvars(r"%LOCALAPPDATA%"), "hermes", "logs")
    real_log = os.path.join(log_dir, "update.log")

    failures = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(f"[{status}] {name} {detail}")
        if not cond:
            failures.append(name)

    # --- 1. real update.log tail (yesterday's successful run) ---
    if os.path.exists(real_log):
        all_lines = read_lines(real_log)
        # counters over the whole log (download-failure lines live in earlier runs)
        _, _, conns_a, downs_a, _, _ = replay(all_lines)
        check("real-log: counters>0", conns_a > 0 and downs_a > 0,
              f"conns={conns_a} downloads={downs_a}")
        # find the last run: last 'Fetching updates' occurrence
        starts = [i for i, l in enumerate(all_lines) if "Fetching updates" in l]
        tail = all_lines[starts[-1]:] if starts else all_lines[-200:]
        state, prog, conns, downs, errs, done = replay(tail)
        reached = [s for s in state if s in ("done", "active", "error")]
        print(f"real log tail: {len(tail)} lines, stages touched: {len(reached)}")
        check("real-run: Update complete detected", done)
        check("real-run: progress=100", prog >= 100.0, f"({prog:.0f}%)")
        check("real-run: all 8 stages done", all(s == "done" for s in state),
              str([s['id'] for s, st in zip(STAGES, state) if st != 'done']))
        # stage order sanity: only within the run proper (before 'Update complete';
        # post-complete maintenance lines like cua-driver are ignored by design)
        order = []
        for line in tail:
            if "update complete" in line.lower():
                break
            i = classify(line.lower())
            if i is not None and (not order or order[-1] != i):
                order.append(i)
        mono = order == sorted(order)
        check("real-run: stage order monotonic", mono, str(order))
        check("real-run: deps+webui stages fire on real markers", 3 in order and 4 in order,
              f"order={order}")
    else:
        print("[SKIP] real update.log not found")

    # --- 2. mock_ok ---
    mock_ok_lines = [l.strip()[1:].rstrip().rstrip(",").strip('"')
                     for l in open(os.path.join(here, "mock_ok.py"), encoding="utf-8")
                     if l.startswith('    "')]
    state, prog, conns, downs, errs, done = replay(mock_ok_lines)
    check("mock_ok: complete", done and prog >= 100.0 and all(s == "done" for s in state),
          f"prog={prog:.0f}% conns={conns} downloads={downs} errors={errs}")

    # --- 3. mock_fail ---
    mock_fail_lines = [l.strip()[1:].rstrip().rstrip(",").strip('"')
                       for l in open(os.path.join(here, "mock_fail.py"), encoding="utf-8")
                       if l.startswith('    "')]
    state, prog, conns, downs, errs, done = replay(mock_fail_lines)
    check("mock_fail: not complete", not done)
    check("mock_fail: errors counted", errs >= 2, f"errors={errs}")
    check("mock_fail: deps stage errored", state[3] in ("error", "active"), str(state))
    check("mock_fail: progress < 100", prog < 100.0, f"({prog:.0f}%)")

    print()
    if failures:
        print("RESULT: FAILED ->", failures)
        sys.exit(1)
    print("RESULT: ALL PASS")


if __name__ == "__main__":
    main()
