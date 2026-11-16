import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hospital.db")
DEFAULT_RESOURCES = [
    ("doctor", "Dr. Smith"), ("doctor", "Dr. Johnson"), ("doctor", "Dr. Lee"), ("doctor", "Dr. Brown"),
    ("nurse", "Nurse Alice"), ("nurse", "Nurse Bob"), ("nurse", "Nurse Charlie"), ("nurse", "Nurse Dana"),
    ("bed", "Floor 1"), ("bed", "Floor 2"), ("bed", "Floor 3"),
]

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS patients(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, arrival INTEGER NOT NULL DEFAULT 0,
            burst INTEGER NOT NULL, priority INTEGER NOT NULL DEFAULT 2,
            created TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS resources(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL CHECK(kind IN ('doctor','nurse','bed')),
            name TEXT NOT NULL UNIQUE);
        CREATE TABLE IF NOT EXISTS runs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            algorithm TEXT, quantum INTEGER, patients INTEGER,
            avg_wait REAL, avg_tat REAL, avg_resp REAL, makespan INTEGER,
            created TEXT DEFAULT CURRENT_TIMESTAMP);
        """)
        if c.execute("SELECT COUNT(*) FROM resources").fetchone()[0] == 0:
            c.executemany("INSERT INTO resources(kind,name) VALUES(?,?)", DEFAULT_RESOURCES)

# ---- patients ----
def add_patient(name, arrival, burst, priority):
    with conn() as c:
        return c.execute("INSERT INTO patients(name,arrival,burst,priority) VALUES(?,?,?,?)",
                         (name, arrival, burst, priority)).lastrowid

def list_patients():
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT id,name,arrival,burst,priority FROM patients ORDER BY id")]

def delete_patient(pid):
    with conn() as c:
        c.execute("DELETE FROM patients WHERE id=?", (pid,))

def clear_patients():
    with conn() as c:
        c.execute("DELETE FROM patients")

# ---- resources ----
def list_resources():
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT id,kind,name FROM resources ORDER BY kind,id")]

def resource_pools():
    pools = {"doctor": [], "nurse": [], "bed": []}
    for r in list_resources():
        pools[r["kind"]].append(r["name"])
    return pools

def add_resource(kind, name):
    with conn() as c:
        return c.execute("INSERT INTO resources(kind,name) VALUES(?,?)", (kind, name)).lastrowid

def delete_resource(rid):
    with conn() as c:
        c.execute("DELETE FROM resources WHERE id=?", (rid,))

# ---- run history ----
def save_run(algorithm, quantum, n, summary):
    with conn() as c:
        c.execute("INSERT INTO runs(algorithm,quantum,patients,avg_wait,avg_tat,avg_resp,makespan) "
                  "VALUES(?,?,?,?,?,?,?)",
                  (algorithm, quantum, n, summary["avg_wait"], summary["avg_tat"],
                   summary["avg_resp"], summary["makespan"]))

def list_runs(limit=100):
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,))]