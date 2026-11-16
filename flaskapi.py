from flask import Flask, jsonify, request, send_from_directory
import database as db
import scheduler as sch

app = Flask(__name__, static_folder="static", static_url_path="/static")
db.init()

SAMPLE = [("Ravi", 0, 30, 2), ("Meena", 2, 12, 1), ("Arun", 3, 20, 3),
          ("Divya", 5, 8, 0), ("Kumar", 6, 25, 2), ("Priya", 8, 15, 1)]


def _patient_from(d):
    name = str(d.get("name", "")).strip()
    try:
        arrival, burst, priority = int(d.get("arrival", 0)), int(d["burst"]), int(d.get("priority", 2))
    except (KeyError, ValueError, TypeError):
        raise ValueError("Arrival, treatment time and priority must be numbers")
    if not name or burst <= 0 or arrival < 0 or priority < 0:
        raise ValueError("Enter a name, arrival >= 0 and treatment time > 0")
    return name, arrival, burst, priority


@app.errorhandler(ValueError)
def bad_request(e):
    return jsonify(error=str(e)), 400


@app.get("/")
def home():
    return send_from_directory("static", "index.html")


@app.get("/api/patients")
def get_patients():
    return jsonify(db.list_patients())


@app.post("/api/patients")
def post_patient():
    return jsonify(id=db.add_patient(*_patient_from(request.get_json(force=True)))), 201


@app.delete("/api/patients/<int:pid>")
def del_patient(pid):
    db.delete_patient(pid)
    return "", 204


@app.delete("/api/patients")
def clear_patients():
    db.clear_patients()
    return "", 204


@app.post("/api/sample")
def sample():
    for s in SAMPLE:
        db.add_patient(*s)
    return jsonify(ok=True), 201


@app.get("/api/resources")
def get_resources():
    return jsonify(db.list_resources())


@app.post("/api/resources")
def post_resource():
    d = request.get_json(force=True)
    if d.get("kind") not in sch.KINDS or not str(d.get("name", "")).strip():
        raise ValueError("Choose a type and enter a name")
    try:
        return jsonify(id=db.add_resource(d["kind"], d["name"].strip())), 201
    except Exception:
        raise ValueError("That resource name already exists")


@app.delete("/api/resources/<int:rid>")
def del_resource(rid):
    db.delete_resource(rid)
    return "", 204


@app.post("/api/schedule")
def schedule():
    d = request.get_json(force=True)
    q = int(d.get("quantum", 5))
    res = sch.run_algorithm(d.get("algorithm", "FCFS"), db.list_patients(), q, db.resource_pools())
    db.save_run(res["algorithm"], q, len(res["rows"]), res["summary"])
    return jsonify(res)


@app.get("/api/compare")
def compare():
    q = int(request.args.get("quantum", 5))
    patients = db.list_patients()
    results = sch.compare_all(patients, q, db.resource_pools())
    best, why = sch.recommend(results)
    for a, r in results.items():
        db.save_run(a, q, len(patients), r["summary"])
    return jsonify(results=results, recommended=best, reason=why)


@app.get("/api/runs")
def runs():
    return jsonify(db.list_runs())


if __name__ == "__main__":
    app.run(port=5000, debug=True)