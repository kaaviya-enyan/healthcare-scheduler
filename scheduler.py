ALGORITHMS = ["FCFS", "SJN", "Priority", "Round Robin"]
KINDS = ["doctor", "nurse", "bed"]

KEYS = {
    "FCFS": lambda p: (p["arrival"], p["id"]),
    "SJN": lambda p: (p["burst"], p["arrival"], p["id"]),
    "Priority": lambda p: (p["priority"], p["arrival"], p["id"]),
}


def _simulate(patients, resources, key=None, quantum=None):
    """Time-aware simulation. A treatment (or a Round Robin slice) can start only
    when one doctor, one nurse and one bed are ALL free at that moment. Each
    resource remembers when it becomes free; among the free ones, the least
    loaded is chosen. Several patients can be treated in parallel."""
    free = {k: {n: 0 for n in resources.get(k, [])} for k in KINDS}   # when each resource is free
    load = {k: {n: 0 for n in resources.get(k, [])} for k in KINDS}   # total minutes worked
    pools = [k for k in KINDS if free[k]]
    rem = {p["id"]: p["burst"] for p in patients}
    events = [(p["arrival"], 0, p["id"], p) for p in patients]        # (time, kind, id, patient)
    ready, slices, t = [], [], 0
    room = 0                                                          # used only when no resources are defined

    while events or ready:
        events.sort(key=lambda e: e[:3])
        while events and events[0][0] <= t:                           # patients who have arrived / returned
            ready.append(events.pop(0)[3])
        if not ready:                                                 # nobody waiting -> jump ahead
            t = events[0][0]
            continue
        nxt = max((min(free[k].values()) for k in pools), default=room)  # earliest time a full set is free
        if nxt > t:                                                   # all staff/beds busy -> wait
            t = nxt
            continue
        p = ready[0] if quantum else min(ready, key=key)
        ready.remove(p)
        run = min(quantum, rem[p["id"]]) if quantum else rem[p["id"]]
        used = {}
        for k in KINDS:
            if not free[k]:
                used[k] = "Unavailable"
                continue
            n = min((n for n in free[k] if free[k][n] <= t),          # only resources free right now
                    key=lambda n: (load[k][n], free[k][n]))           # ...then the least loaded
            free[k][n] = t + run
            load[k][n] += run
            used[k] = n
        if not pools:
            room = t + run                                            # no resources defined: one treatment at a time
        slices.append({"pid": p["id"], "name": p["name"], "start": t, "end": t + run, **used})
        rem[p["id"]] -= run
        if rem[p["id"]] > 0:                                          # Round Robin: back to the queue after the slice
            events.append((t + run, 1, p["id"], p))
    capacity = max(1, min((len(free[k]) for k in pools), default=1))  # max parallel treatments
    return slices, load, capacity


def _rows(patients, slices):
    info = {}
    for s in slices:
        d = info.setdefault(s["pid"], {"start": s["start"], "end": s["end"], **{k: [] for k in KINDS}})
        d["end"] = max(d["end"], s["end"])
        for k in KINDS:
            if s[k] not in d[k]:
                d[k].append(s[k])
    rows = []
    for p in patients:
        d = info[p["id"]]
        tat = d["end"] - p["arrival"]
        rows.append({
            "id": p["id"], "name": p["name"], "priority": p["priority"],
            "arrival": p["arrival"], "burst": p["burst"],
            "start": d["start"], "completion": d["end"],
            "turnaround": tat, "waiting": tat - p["burst"],
            "response": d["start"] - p["arrival"],
            "doctor": " / ".join(d["doctor"]), "nurse": " / ".join(d["nurse"]),
            "bed": " / ".join(d["bed"]),
        })
    return rows


def _summary(rows, slices, capacity):
    n = len(rows)
    makespan = max(s["end"] for s in slices)
    busy = sum(s["end"] - s["start"] for s in slices)
    emerg = [r["response"] for r in rows if r["priority"] == 0]
    return {
        "avg_wait": round(sum(r["waiting"] for r in rows) / n, 2),
        "avg_tat": round(sum(r["turnaround"] for r in rows) / n, 2),
        "avg_resp": round(sum(r["response"] for r in rows) / n, 2),
        "makespan": makespan,
        "capacity": capacity,
        "utilisation": round(busy / (makespan * capacity) * 100, 1),
        "emergency_response": round(sum(emerg) / len(emerg), 2) if emerg else None,
    }


def run_algorithm(name, patients, quantum=5, resources=None):
    if not patients:
        raise ValueError("No patients to schedule")
    resources = resources or {}
    if name in KEYS:
        slices, load, cap = _simulate(patients, resources, key=KEYS[name])
    elif name == "Round Robin":
        slices, load, cap = _simulate(patients, resources, quantum=max(1, int(quantum)))
    else:
        raise ValueError(f"Unknown algorithm: {name}")
    rows = _rows(patients, slices)
    return {"algorithm": name, "quantum": quantum, "slices": slices, "rows": rows,
            "summary": _summary(rows, slices, cap), "workload": load}


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