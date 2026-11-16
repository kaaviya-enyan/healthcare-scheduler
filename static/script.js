const $ = s => document.querySelector(s);
const PRI = {0: "Emergency", 1: "Urgent", 2: "Routine", 3: "Low"};
const PCOL = ["#ef4444", "#f59e0b", "#3b82f6", "#94a3b8"];
const ALGOS = {
  "FCFS": ["First-Come, First-Served", "Treats patients in the order they arrive.", "Use when: no one is urgent and fairness by arrival matters."],
  "SJN": ["Shortest Job Next", "Treats the shortest treatment first.", "Use when: you want the lowest average waiting time."],
  "Priority": ["Priority", "Treats the most urgent patient first.", "Use when: emergencies must be handled immediately."],
  "Round Robin": ["Round Robin", "Gives everyone a small turn in rotation.", "Use when: many patients and fair sharing matters."]
};
const TITLES = {
  dashboard: ["Dashboard", "Overview of your patients, staff and recent scheduling results"],
  patients: ["Patients", "Step 1 · Add who is waiting for treatment"],
  schedule: ["Schedule", "Step 2 · See the treatment order for one algorithm"],
  compare: ["Compare algorithms", "Step 3 · Find the best algorithm for your patients"],
  resources: ["Resources", "Doctors, nurses and beds that are assigned automatically"],
  history: ["History", "Every scheduling run is saved here"]
};
const COLORS = ["#2563eb", "#16a34a", "#f59e0b", "#9333ea", "#0891b2", "#db2777", "#65a30d", "#ea580c"];
let selected = "FCFS";

async function api(url, method = "GET", body) {
  const r = await fetch(url, {method, headers: {"Content-Type": "application/json"}, body: body ? JSON.stringify(body) : undefined});
  if (r.status === 204) return null;
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || "Something went wrong");
  return data;
}
function toast(msg, err) {
  const t = $("#toast"); t.textContent = msg; t.className = "show" + (err ? " err" : "");
  setTimeout(() => t.className = "", 2500);
}
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const tag = p => `<span class="tag p${p}">${PRI[p] || p}</span>`;
const tbl = (el, head, rows) => el.innerHTML = `<tr>${head.map(h => `<th>${h}</th>`).join("")}</tr>` +
  (rows.length ? rows.join("") : `<tr><td colspan="${head.length}" style="text-align:center;color:#64748b">Nothing here yet</td></tr>`);

/* ---------- navigation ---------- */
function show(tab) {
  document.querySelectorAll(".nav").forEach(b => b.classList.toggle("active", b.dataset.tab === tab));
  document.querySelectorAll(".panel").forEach(p => p.classList.toggle("active", p.id === tab));
  $("#pgTitle").textContent = TITLES[tab][0]; $("#pgSub").textContent = TITLES[tab][1];
  if (tab === "history") loadHistory();
  if (tab === "dashboard") loadDashboard();
  window.scrollTo(0, 0);
}
document.querySelectorAll(".nav").forEach(b => b.onclick = () => show(b.dataset.tab));
document.querySelectorAll("[data-go]").forEach(b => b.onclick = () => show(b.dataset.go));

/* ---------- dashboard ---------- */
function donut(counts) {
  const total = counts.reduce((a, b) => a + b, 0), C = 2 * Math.PI * 40;
  let off = 0, seg = `<circle r="40" cx="60" cy="60" fill="none" stroke="#e2e8f0" stroke-width="18"/>`;
  if (total) seg = counts.map((c, i) => {
    const len = c / total * C;
    const s = `<circle r="40" cx="60" cy="60" fill="none" stroke="${PCOL[i]}" stroke-width="18" stroke-dasharray="${len} ${C - len}" stroke-dashoffset="${-off}" transform="rotate(-90 60 60)"/>`;
    off += len; return s;
  }).join("");
  return `<svg viewBox="0 0 120 120" width="150">${seg}<text x="60" y="66" text-anchor="middle" font-size="20" font-weight="700">${total}</text></svg>`;
}
async function loadDashboard() {
  const [ps, rs, runs] = await Promise.all([api("/api/patients"), api("/api/resources"), api("/api/runs")]);
  $("#kPat").textContent = ps.length;
  $("#kEm").textContent = ps.filter(p => p.priority === 0).length;
  $("#kAvg").textContent = (ps.length ? Math.round(ps.reduce((a, p) => a + p.burst, 0) / ps.length) : 0) + " min";
  $("#kStaff").textContent = rs.length;
  const counts = [0, 1, 2, 3].map(k => ps.filter(p => p.priority === k).length);
  $("#donut").innerHTML = donut(counts);
  $("#legend").innerHTML = counts.map((c, i) => `<div class="lg"><i style="background:${PCOL[i]}"></i>${PRI[i]}: <b>${c}</b></div>`).join("");

  const algosRun = new Set(runs.map(r => r.algorithm));
  const steps = [
    [ps.length > 0, "Add patients (or load the sample data)", "patients"],
    [runs.length > 0, "Run one algorithm and read the timeline", "schedule"],
    [["FCFS", "SJN", "Priority", "Round Robin"].every(a => algosRun.has(a)), "Compare all four algorithms", "compare"]];
  $("#checklist").innerHTML = steps.map((s, i) => `<li class="${s[0] ? "done" : ""}" data-go="${s[2]}"><span>${s[0] ? "✓" : i + 1}</span>${s[1]}</li>`).join("");
  document.querySelectorAll("#checklist li").forEach(li => li.onclick = () => show(li.dataset.go));

  const r = runs[0];
  $("#latest").innerHTML = r ? `<p class="hint">${r.algorithm} on ${r.patients} patients</p><div class="mini">
    <div><small>Avg waiting</small><b>${r.avg_wait} min</b></div><div><small>Avg turnaround</small><b>${r.avg_tat} min</b></div>
    <div><small>Avg response</small><b>${r.avg_resp} min</b></div><div><small>Total time</small><b>${r.makespan} min</b></div></div>`
    : `<p class="hint">No runs yet. Add patients, then press <b>Run schedule</b>.</p>`;
  tbl($("#recent"), ["Algorithm", "Patients", "Avg wait", "Total time"], runs.slice(0, 5).map(r =>
    `<tr><td>${r.algorithm}</td><td>${r.patients}</td><td>${r.avg_wait}</td><td>${r.makespan}</td></tr>`));
}

/* ---------- patients ---------- */
async function loadPatients() {
  const ps = await api("/api/patients");
  $("#pCount").textContent = ps.length;
  tbl($("#pTable"), ["#", "Name", "Arrival", "Treatment", "Priority", ""], ps.map(p =>
    `<tr><td>${p.id}</td><td>${esc(p.name)}</td><td>${p.arrival} min</td><td>${p.burst} min</td><td>${tag(p.priority)}</td>
     <td><button class="x" title="Remove" onclick="delPatient(${p.id})">✕</button></td></tr>`));
  loadDashboard();
}
async function delPatient(id) { await api("/api/patients/" + id, "DELETE"); loadPatients(); }
$("#patientForm").onsubmit = async e => {
  e.preventDefault();
  const pri = +$("#pPri").value, name = $("#pName").value;
  try {
    await api("/api/patients", "POST", {name, arrival: +$("#pArr").value, burst: +$("#pBurst").value, priority: pri});
    e.target.reset(); $("#pPri").value = "2";
    toast(pri === 0 ? "🚨 Emergency patient added: " + name : "Patient added");
    if (pri === 0) beep();
    loadPatients();
  } catch (err) { toast(err.message, true); }
};
$("#sampleBtn").onclick = async () => { await api("/api/sample", "POST"); toast("Sample patients loaded"); loadPatients(); };
$("#clearBtn").onclick = async () => { if (confirm("Remove all patients?")) { await api("/api/patients", "DELETE"); loadPatients(); } };
function beep() {
  try {
    const c = new (window.AudioContext || window.webkitAudioContext)();
    [0, .35, .7].forEach(t => { const o = c.createOscillator(); o.frequency.value = 1000; o.connect(c.destination);
      o.start(c.currentTime + t); o.stop(c.currentTime + t + .25); });
  } catch (e) {}
}

/* ---------- schedule ---------- */
function drawAlgoCards() {
  $("#algoCards").innerHTML = Object.entries(ALGOS).map(([k, v]) =>
    `<div class="algo ${k === selected ? "sel" : ""}" data-k="${k}"><b>${v[0]}</b><p>${v[1]}</p><p class="use">${v[2]}</p></div>`).join("");
  document.querySelectorAll(".algo").forEach(c => c.onclick = () => { selected = c.dataset.k; drawAlgoCards(); });
  $("#qBox").style.display = selected === "Round Robin" ? "flex" : "none";
}
$("#runBtn").onclick = async () => {
  try {
    const res = await api("/api/schedule", "POST", {algorithm: selected, quantum: +$("#quantum").value});
    $("#schedEmpty").classList.add("hidden"); $("#schedResult").classList.remove("hidden");
    renderSchedule(res);
  } catch (err) { toast(err.message === "No patients to schedule" ? "Add patients first (step 1)" : err.message, true); }
};
function renderSchedule(res) {
  const s = res.summary;
  $("#stats").innerHTML = [["Avg waiting", s.avg_wait + " min"], ["Avg turnaround", s.avg_tat + " min"], ["Avg response", s.avg_resp + " min"],
    ["Total time", s.makespan + " min"], ["Utilisation", s.utilisation + "%"]].map(x => `<div class="stat"><span>${x[0]}</span><b>${x[1]}</b></div>`).join("");
  gantt(res);
  tbl($("#rTable"), ["Patient", "Priority", "Arrives", "Starts", "Finishes", "Waited", "Doctor", "Nurse", "Bed"], res.rows.map(r =>
    `<tr><td>${esc(r.name)}</td><td>${tag(r.priority)}</td><td>${r.arrival}</td><td>${r.start}</td><td>${r.completion}</td><td>${r.waiting} min</td>
     <td>${esc(r.doctor)}</td><td>${esc(r.nurse)}</td><td>${esc(r.bed)}</td></tr>`));
  const max = Math.max(1, ...Object.values(res.workload).flatMap(p => Object.values(p)));
  $("#workload").innerHTML = Object.entries(res.workload).map(([k, pool]) => `<b>${k[0].toUpperCase() + k.slice(1)}s</b>` +
    Object.entries(pool).map(([n, m]) => `<div class="wl"><span class="n">${esc(n)}</span><div class="t"><div class="f" style="width:${m / max * 100}%"></div></div><span>${m} min</span></div>`).join("")).join("");
}
function gantt(res) {
  const W = 1000, L = 90, R = 20, T = 10, rowH = 34, n = res.rows.length, H = T + n * rowH + 40;
  const end = res.summary.makespan, sx = t => L + t / end * (W - L - R);
  const step = Math.max(1, Math.ceil(end / 15));
  const idx = {}, prio = {}; res.rows.forEach((r, i) => { idx[r.id] = i; prio[r.id] = r.priority; });
  let g = "";
  for (let t = 0; t <= end; t += step) g += `<line x1="${sx(t)}" x2="${sx(t)}" y1="${T}" y2="${T + n * rowH}" stroke="#e2e8f0"/><text x="${sx(t)}" y="${H - 14}" font-size="12" text-anchor="middle" fill="#64748b">${t}</text>`;
  res.rows.forEach((r, i) => g += `<text x="${L - 8}" y="${T + i * rowH + 21}" font-size="13" text-anchor="end">${esc(r.name)}</text>`);
  res.slices.forEach(s => {
    const y = T + idx[s.pid] * rowH + 4, e = prio[s.pid] === 0;
    g += `<rect x="${sx(s.start)}" y="${y}" width="${Math.max(2, sx(s.end) - sx(s.start))}" height="${rowH - 8}" rx="4" fill="${COLORS[s.pid % COLORS.length]}"
      stroke="${e ? "#dc2626" : "#fff"}" stroke-width="${e ? 3 : 1}"><title>${esc(s.name)}: ${s.start} to ${s.end}</title></rect>`;
  });
  g += `<text x="${W / 2}" y="${H - 1}" font-size="12" text-anchor="middle" fill="#64748b">Time (minutes)</text>`;
  $("#gantt").innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="100%">${g}</svg>`;
}

/* ---------- compare ---------- */
$("#cmpBtn").onclick = async () => {
  try {
    const d = await api("/api/compare?quantum=" + (+$("#quantum").value || 5));
    $("#cmpResult").classList.remove("hidden");
    $("#recBox").innerHTML = `✅ <b>Recommended: ${ALGOS[d.recommended][0]}</b><br>Reason: ${d.reason}.`;
    const R = d.results;
    tbl($("#cTable"), ["Algorithm", "Avg wait", "Avg turnaround", "Avg response", "Total time", "Utilisation", "Emergency response"],
      Object.entries(R).map(([a, r]) => { const s = r.summary;
        return `<tr class="${a === d.recommended ? "best" : ""}"><td>${a}${a === d.recommended ? " ⭐" : ""}</td><td>${s.avg_wait}</td><td>${s.avg_tat}</td><td>${s.avg_resp}</td><td>${s.makespan}</td><td>${s.utilisation}%</td><td>${s.emergency_response ?? "-"}</td></tr>`; }));
    let html = "";
    [["avg_wait", "Average waiting time"], ["avg_tat", "Average turnaround time"], ["avg_resp", "Average response time"]].forEach(([k, lbl], i) => {
      const max = Math.max(1, ...Object.values(R).map(r => r.summary[k]));
      html += `<p class="hint" style="margin-top:12px"><b>${lbl}</b></p>` + Object.entries(R).map(([a, r]) =>
        `<div class="bar"><span class="n">${a}</span><div class="t"><div class="f" style="width:${r.summary[k] / max * 100}%;background:${COLORS[i]}"></div></div><span class="v">${r.summary[k]}</span></div>`).join("");
    });
    $("#barChart").innerHTML = html;
  } catch (err) { toast(err.message === "No patients to schedule" ? "Add patients first (step 1)" : err.message, true); }
};

/* ---------- resources ---------- */
async function loadResources() {
  const rs = await api("/api/resources");
  tbl($("#resTable"), ["Type", "Name", ""], rs.map(r =>
    `<tr><td>${r.kind}</td><td>${esc(r.name)}</td><td><button class="x" onclick="delRes(${r.id})">✕</button></td></tr>`));
  loadDashboard();
}
async function delRes(id) { await api("/api/resources/" + id, "DELETE"); loadResources(); }
$("#resForm").onsubmit = async e => {
  e.preventDefault();
  try { await api("/api/resources", "POST", {kind: $("#rKind").value, name: $("#rName").value}); e.target.reset(); toast("Added"); loadResources(); }
  catch (err) { toast(err.message, true); }
};

/* ---------- history ---------- */
async function loadHistory() {
  const rs = await api("/api/runs");
  tbl($("#hTable"), ["Run", "Algorithm", "Quantum", "Patients", "Avg wait", "Avg TAT", "Avg resp", "Total time", "When"], rs.map(r =>
    `<tr><td>${r.id}</td><td>${r.algorithm}</td><td>${r.quantum}</td><td>${r.patients}</td><td>${r.avg_wait}</td><td>${r.avg_tat}</td><td>${r.avg_resp}</td><td>${r.makespan}</td><td>${r.created}</td></tr>`));
}

show("dashboard"); drawAlgoCards(); loadPatients(); loadResources();