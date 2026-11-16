# Healthcare CPU Scheduling Simulator

A web dashboard that applies CPU scheduling algorithms to hospital patient treatment. It decides **who is treated first** and **which doctor, nurse and bed** they get, then compares four algorithms and recommends the best one.

## Why this project
Hospitals have many patients with different arrival times, treatment durations and urgency, but limited staff and beds. Poor ordering means long waits and delayed emergency care. This project uses classic Operating System scheduling ideas to manage that.

## Features
- **Four algorithms:** FCFS, Shortest Job Next (SJN), Priority, and Round Robin (adjustable time quantum)
- **Resource-aware allocation:** a treatment starts only when a doctor, nurse and bed are all free; the least-loaded free staff are chosen
- **Metrics:** waiting, turnaround and response time, total time and utilisation
- **Compare page:** runs all four algorithms on the same patients and recommends one, giving priority to emergency response
- **Dashboard UI:** KPI cards, Gantt chart, staff workload, run history and a getting-started checklist
- **Emergency handling:** priority 0 patients are highlighted with a red outline and an alert sound
- **Saved data:** patients, staff and past runs are stored in SQLite

## Tech stack
| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| API | FastAPI, Uvicorn |
| Backend | Python (scheduling engine) |
| Database | SQLite |

**Architecture:** Browser → FastAPI REST API → Scheduling engine → SQLite

## Project structure
```
├── api.py          # FastAPI routes
├── scheduler.py    # scheduling algorithms and resource allocation
├── database.py     # SQLite functions
└── static/
    ├── index.html
    ├── style.css
    └── script.js
```

## How to run
```bash
git clone https://github.com/kaaviya-enyan/healthcare-scheduler.git
cd healthcare-scheduler
pip install fastapi uvicorn
python api.py
```
Open **http://127.0.0.1:5000** in your browser. API docs are at **http://127.0.0.1:5000/docs**.

## How to use
1. **Patients:** click *Load sample patients* or add your own (arrival time, treatment time, priority)
2. **Schedule:** choose an algorithm and click *Run schedule* to see the timeline
3. **Compare:** click *Compare now* to see all four side by side with a recommendation
4. **Resources:** add or remove doctors, nurses and beds. Fewer resources make the differences between algorithms clearer

## Algorithms
| Algorithm | Treats first | Best when |
|---|---|---|
| FCFS | Earliest arrival | No one is urgent |
| SJN | Shortest treatment | Minimising average waiting time |
| Priority | Most urgent | Emergencies must go first |
| Round Robin | Everyone in turn (time slices) | Fair sharing among many patients |

## Limitations
- It is a simulation using sample data, not a live hospital system
- Priority scheduling is non-preemptive, so an emergency waits if all beds are in use
- Every treatment needs one doctor, one nurse and one bed together; specialities and shifts are not modelled

## Future scope
- Aging to prevent starvation of low-priority patients
- Preemptive priority for emergencies
- Login and roles (doctor, nurse, admin)
- Treatment time prediction using machine learning
- SMS or email alerts for emergencies

## Author
Kaaviya E