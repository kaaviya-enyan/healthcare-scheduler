import os
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

import database as db
import scheduler as sch

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")

app = FastAPI(title="Healthcare Scheduling Simulator API")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
db.init()

SAMPLE = [("Ravi", 0, 30, 2), ("Meena", 2, 12, 1), ("Arun", 3, 20, 3),
          ("Divya", 5, 8, 0), ("Kumar", 6, 25, 2), ("Priya", 8, 15, 1)]


# ---------- request models ----------
class PatientIn(BaseModel):
    name: str
    arrival: int = 0
    burst: int
    priority: int = 2


class ResourceIn(BaseModel):
    kind: str
    name: str


class ScheduleIn(BaseModel):
    algorithm: str = "FCFS"
    quantum: int = 5


# ---------- errors (the frontend reads {"error": "..."}) ----------
@app.exception_handler(ValueError)
async def value_error(_: Request, e: ValueError):
    return JSONResponse({"error": str(e)}, status_code=400)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, e: RequestValidationError):
    return JSONResponse({"error": "Please check the values you entered"}, status_code=400)


# ---------- pages ----------
@app.get("/", include_in_schema=False)
def home():
    return FileResponse(os.path.join(STATIC, "index.html"))


# ---------- patients ----------
@app.get("/api/patients")
def get_patients():
    return db.list_patients()


@app.post("/api/patients", status_code=201)
def post_patient(p: PatientIn):
    name = p.name.strip()
    if not name or p.burst <= 0 or p.arrival < 0 or p.priority < 0:
        raise ValueError("Enter a name, arrival >= 0 and treatment time > 0")
    return {"id": db.add_patient(name, p.arrival, p.burst, p.priority)}


@app.delete("/api/patients/{pid}", status_code=204)
def del_patient(pid: int):
    db.delete_patient(pid)
    return Response(status_code=204)


@app.delete("/api/patients", status_code=204)
def clear_patients():
    db.clear_patients()
    return Response(status_code=204)


@app.post("/api/sample", status_code=201)
def sample():
    for s in SAMPLE:
        db.add_patient(*s)
    return {"ok": True}


# ---------- resources ----------
@app.get("/api/resources")
def get_resources():
    return db.list_resources()


@app.post("/api/resources", status_code=201)
def post_resource(r: ResourceIn):
    if r.kind not in sch.KINDS or not r.name.strip():
        raise ValueError("Choose a type and enter a name")
    try:
        return {"id": db.add_resource(r.kind, r.name.strip())}
    except Exception:
        raise ValueError("That resource name already exists")


@app.delete("/api/resources/{rid}", status_code=204)
def del_resource(rid: int):
    db.delete_resource(rid)
    return Response(status_code=204)


# ---------- scheduling ----------
@app.post("/api/schedule")
def schedule(s: ScheduleIn):
    res = sch.run_algorithm(s.algorithm, db.list_patients(), s.quantum, db.resource_pools())
    db.save_run(res["algorithm"], s.quantum, len(res["rows"]), res["summary"])
    return res


@app.get("/api/compare")
def compare(quantum: int = 5):
    patients = db.list_patients()
    results = sch.compare_all(patients, quantum, db.resource_pools())
    best, why = sch.recommend(results)
    for a, r in results.items():
        db.save_run(a, quantum, len(patients), r["summary"])
    return {"results": results, "recommended": best, "reason": why}


@app.get("/api/runs")
def runs():
    return db.list_runs()


if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=5000, reload=True)