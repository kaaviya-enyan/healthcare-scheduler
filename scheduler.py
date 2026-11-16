ALGORITHMS = ["FCFS", "SJN", "Priority", "Round Robin"]
KINDS = ["doctor", "nurse", "bed"]


def _slice(p, start, end):
    return {"pid": p["id"], "name": p["name"], "start": start, "end": end}


def _non_preemptive(patients, key):
    pending = sorted(patients, key=lambda p: (p["arrival"], p["id"]))
    t, slices = 0, []
    while pending:
        ready = [p for p in pending if p["arrival"] <= t]
        if not ready:                       # CPU idle -> jump to next arrival
            t = min(p["arrival"] for p in pending)
            continue
        p = min(ready, key=key)
        pending.remove(p)
        slices.append(_slice(p, t, t + p["burst"]))
        t += p["burst"]
    return slices


def _round_robin(patients, quantum):
    incoming = sorted(patients, key=lambda p: (p["arrival"], p["id"]))
    rem = {p["id"]: p["burst"] for p in patients}
    queue, slices, t, i = [], [], 0, 0
    while i < len(incoming) or queue:
        while i < len(incoming) and incoming[i]["arrival"] <= t:
            queue.append(incoming[i]); i += 1
        if not queue:
            t = incoming[i]["arrival"]
            continue
        p = queue.pop(0)
        run = min(quantum, rem[p["id"]])
        slices.append(_slice(p, t, t + run))
        t += run
        rem[p["id"]] -= run
        while i < len(incoming) and incoming[i]["arrival"] <= t:
            queue.append(incoming[i]); i += 1
        if rem[p["id"]] > 0:
            queue.append(p)
    return slices


def allocate(patients, slices, resources):
    """Workload-balanced allocation: each patient gets the least-loaded
    doctor, nurse and bed at the moment their treatment first starts."""
    load = {k: {n: 0 for n in resources.get(k, [])} for k in KINDS}
    first = {}
    for s in slices:
        first.setdefault(s["pid"], s["start"])
    burst = {p["id"]: p["burst"] for p in patients}
    alloc = {}
    for pid in sorted(first, key=first.get):
        alloc[pid] = {}
        for kind in KINDS:
            pool = load[kind]
            if pool:
                n = min(pool, key=pool.get)
                pool[n] += burst[pid]
                alloc[pid][kind] = n
            else:
                alloc[pid][kind] = "Unavailable"
    return alloc, load


def _rows(patients, slices, alloc):
    first, last = {}, {}
    for s in slices:
        first.setdefault(s["pid"], s["start"])
        last[s["pid"]] = s["end"]
    rows = []
    for p in patients:
        ct = last[p["id"]]
        tat = ct - p["arrival"]
        rows.append({
            "id": p["id"], "name": p["name"], "priority": p["priority"],
            "arrival": p["arrival"], "burst": p["burst"],
            "start": first[p["id"]], "completion": ct,
            "turnaround": tat, "waiting": tat - p["burst"],
            "response": first[p["id"]] - p["arrival"],
            "doctor": alloc[p["id"]]["doctor"], "nurse": alloc[p["id"]]["nurse"],
            "bed": alloc[p["id"]]["bed"],
        })
    return rows


def _summary(rows, slices):
    n = len(rows)
    makespan = max(s["end"] for s in slices)
    busy = sum(s["end"] - s["start"] for s in slices)
    emerg = [r["response"] for r in rows if r["priority"] == 0]
    return {
        "avg_wait": round(sum(r["waiting"] for r in rows) / n, 2),
        "avg_tat": round(sum(r["turnaround"] for r in rows) / n, 2),
        "avg_resp": round(sum(r["response"] for r in rows) / n, 2),
        "makespan": makespan,
        "utilisation": round(busy / makespan * 100, 1),
        "emergency_response": round(sum(emerg) / len(emerg), 2) if emerg else None,
    }


def run_algorithm(name, patients, quantum=5, resources=None):
    if not patients:
        raise ValueError("No patients to schedule")
    if name == "FCFS":
        slices = _non_preemptive(patients, lambda p: (p["arrival"], p["id"]))
    elif name == "SJN":
        slices = _non_preemptive(patients, lambda p: (p["burst"], p["arrival"], p["id"]))
    elif name == "Priority":
        slices = _non_preemptive(patients, lambda p: (p["priority"], p["arrival"], p["id"]))
    elif name == "Round Robin":
        slices = _round_robin(patients, max(1, int(quantum)))
    else:
        raise ValueError(f"Unknown algorithm: {name}")
    alloc, workload = allocate(patients, slices, resources or {})
    rows = _rows(patients, slices, alloc)
    return {"algorithm": name, "quantum": quantum, "slices": slices, "rows": rows,
            "summary": _summary(rows, slices), "workload": workload}


def compare_all(patients, quantum=5, resources=None):
    return {a: run_algorithm(a, patients, quantum, resources) for a in ALGORITHMS}


def recommend(results):
    """Emergency response first (if any priority-0 patients), then average waiting."""
    def key(item):
        s = item[1]["summary"]
        return (s["emergency_response"] if s["emergency_response"] is not None else 0, s["avg_wait"])
    best, res = min(results.items(), key=key)
    s = res["summary"]
    why = f"lowest average waiting time ({s['avg_wait']})"
    if s["emergency_response"] is not None:
        why = f"fastest emergency response ({s['emergency_response']}) and {why}"
    return best, why