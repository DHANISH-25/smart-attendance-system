import { useState, useEffect, useRef } from "react";

// ─── API FUNCTIONS ────────────────────────────────────────────────────────────
const BASE = "http://localhost:5000/api";
const api = {
  get:  (url)       => fetch(`${BASE}${url}`).then(r => r.json()).catch(() => ({ success: false, message: "Flask server not running!" })),
  post: (url, body) => fetch(`${BASE}${url}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(r => r.json()).catch(() => ({ success: false, message: "Flask server not running!" })),
  del:  (url)       => fetch(`${BASE}${url}`, { method: "DELETE" }).then(r => r.json()).catch(() => ({ success: false, message: "Flask server not running!" })),
};

// ─── AVATAR ───────────────────────────────────────────────────────────────────
const Avatar = ({ name, size = 40 }) => {
  const colors = [["#FF6B6B","#FF8E53"],["#4ECDC4","#44A08D"],["#FFC837","#FF8008"],["#667EEA","#764BA2"],["#F093FB","#F5576C"],["#11998e","#38ef7d"]];
  const [c1,c2] = colors[name.charCodeAt(0) % colors.length];
  const initials = name.split(" ").map(n=>n[0]).join("").slice(0,2).toUpperCase();
  return <div style={{ width:size, height:size, borderRadius:"50%", background:`linear-gradient(135deg,${c1},${c2})`, display:"flex", alignItems:"center", justifyContent:"center", color:"#fff", fontWeight:700, fontSize:size*0.35, flexShrink:0, boxShadow:`0 4px 15px ${c1}55` }}>{initials}</div>;
};

// ─── STAT CARD ────────────────────────────────────────────────────────────────
const StatCard = ({ label, value, icon, color, delay=0 }) => (
  <div style={{ background:"rgba(255,255,255,0.07)", backdropFilter:"blur(20px)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:20, padding:"24px 28px", animation:`slideUp 0.6s ease ${delay}s both`, position:"relative", overflow:"hidden" }}>
    <div style={{ position:"absolute", top:-20, right:-20, width:80, height:80, borderRadius:"50%", background:`${color}22` }} />
    <div style={{ fontSize:28, marginBottom:8 }}>{icon}</div>
    <div style={{ fontSize:36, fontWeight:800, color, fontFamily:"'Syne',sans-serif" }}>{value}</div>
    <div style={{ color:"rgba(255,255,255,0.6)", fontSize:13, marginTop:4, fontWeight:500 }}>{label}</div>
  </div>
);

// ─── NOTIFICATION ─────────────────────────────────────────────────────────────
const Notif = ({ notif }) => notif ? (
  <div style={{ position:"fixed", top:20, right:20, zIndex:9999, background: notif.type==="success" ? "linear-gradient(135deg,#11998e,#38ef7d)" : "linear-gradient(135deg,#FF416C,#FF4B2B)", padding:"14px 24px", borderRadius:12, boxShadow:"0 10px 40px rgba(0,0,0,0.3)", animation:"slideUp 0.3s ease", fontWeight:600, fontSize:14 }}>
    {notif.type==="success"?"✅":"❌"} {notif.msg}
  </div>
) : null;

// ─── LOADING SPINNER ──────────────────────────────────────────────────────────
const Spinner = () => (
  <div style={{ display:"flex", justifyContent:"center", padding:40 }}>
    <div style={{ width:40, height:40, border:"3px solid rgba(255,255,255,0.1)", borderTop:"3px solid #667EEA", borderRadius:"50%", animation:"spin 0.8s linear infinite" }} />
  </div>
);

// ─── MAIN APP ─────────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage]           = useState("dashboard");
  const [students, setStudents]   = useState([]);
  const [todayData, setTodayData] = useState(null);
  const [allDates, setAllDates]   = useState([]);
  const [selDate, setSelDate]     = useState("");
  const [dateData, setDateData]   = useState(null);
  const [camStatus, setCamStatus] = useState({ active:false, message:"" });
  const [notif, setNotif]         = useState(null);
  const [loading, setLoading]     = useState({});
  const [regName, setRegName]     = useState("");
  const [search, setSearch]       = useState("");
  const pollRef                   = useRef(null);

  // ── Notification helper ──────────────────────────────────────────────────────
  const notify = (msg, type="success") => {
    setNotif({ msg, type });
    setTimeout(() => setNotif(null), 3500);
  };

  const setLoad = (key, val) => setLoading(p => ({ ...p, [key]:val }));

  // ── Load data on mount ───────────────────────────────────────────────────────
useEffect(() => {
    loadStudents();
    loadToday();
    loadDates();
    // Sync camera state on load
    api.get("/camera-status").then(res => {
        if (res.active !== undefined) setCamStatus(res);
    });
}, []);

  // ── Poll camera status when active ──────────────────────────────────────────
  useEffect(() => {
    if (camStatus.active) {
      pollRef.current = setInterval(async () => {
        const res = await api.get("/camera-status");
        setCamStatus(res);
        if (res.message?.includes("marked Present")) {
          loadToday(); // refresh attendance when someone is marked
        }
      }, 1500);
    } else {
      clearInterval(pollRef.current);
    }
    return () => clearInterval(pollRef.current);
  }, [camStatus.active]);

  // ── API CALLS ────────────────────────────────────────────────────────────────
  const loadStudents = async () => {
    setLoad("students", true);
    const res = await api.get("/students");
    if (res.success) setStudents(res.students);
    setLoad("students", false);
  };

  const loadToday = async () => {
    const res = await api.get("/attendance/today");
    if (res.success) setTodayData(res);
  };

  const loadDates = async () => {
    const res = await api.get("/attendance-dates");
    if (res.success) { setAllDates(res.dates); if (res.dates[0]) setSelDate(res.dates[0]); }
  };

  const loadDateData = async (d) => {
    setLoad("date", true);
    const res = await api.get(`/attendance/${d}`);
    if (res.success) setDateData(res);
    setLoad("date", false);
  };

  const handleRegister = async () => {
    if (!regName.trim()) { notify("Enter student name!", "error"); return; }
    setLoad("register", true);
    notify("📷 Camera opening... Look at the camera!", "success");
    const res = await api.post("/register", { name: regName.trim() });
    setLoad("register", false);
    if (res.success) {
      notify(res.message);
      setRegName("");
      loadStudents();
    } else {
      notify(res.message || "Registration failed!", "error");
    }
  };

  const handleStartCamera = async () => {
	setLoad("camera", true);
	const res = await api.post("/start-attendance", {});
	setLoad("camera", false);
	if (res.success) {
		setCamStatus({ active: true, message: "Camera starting..." });
		notify("Attendance camera started!");
		// Force poll immediately
		setTimeout(async () => {
			const status = await api.get("/camera-status");
			setCamStatus(status);
		}, 1000);
	} else {
		notify(res.message, "error");
	}
};

  const handleStopCamera = async () => {
    const res = await api.post("/stop-attendance", {});
    if (res.success) { setCamStatus({ active:false, message:"" }); notify("Camera stopped!", "error"); loadToday(); }
  };

  const handleDeleteStudent = async (name) => {
    const res = await api.del(`/students/${encodeURIComponent(name)}`);
    if (res.success) { notify(`${name} removed!`, "error"); loadStudents(); }
    else notify(res.message, "error");
  };

  // ── Filtered data ────────────────────────────────────────────────────────────
  const filtStudents = students.filter(s => s.name.toLowerCase().includes(search.toLowerCase()));
  const filtRecords  = (dateData?.records || []).filter(r => r.Name?.toLowerCase().includes(search.toLowerCase()));

  // ── NAV ITEMS ────────────────────────────────────────────────────────────────
  const navItems = [
    { id:"dashboard", icon:"⚡", label:"Dashboard"  },
    { id:"attendance",icon:"📋", label:"Attendance" },
    { id:"students",  icon:"👥", label:"Students"   },
    { id:"register",  icon:"➕", label:"Register"   },
    { id:"camera",    icon:"📷", label:"Camera"     },
  ];

  return (
    <div style={{ minHeight:"100vh", background:"linear-gradient(135deg,#0f0c29 0%,#1a1a4e 40%,#24243e 100%)", fontFamily:"'DM Sans',sans-serif", color:"#fff" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap');
        * { box-sizing:border-box; margin:0; padding:0; }
        @keyframes slideUp { from{opacity:0;transform:translateY(30px)} to{opacity:1;transform:translateY(0)} }
        @keyframes fadeIn  { from{opacity:0} to{opacity:1} }
        @keyframes spin    { to{transform:rotate(360deg)} }
        @keyframes pulse   { 0%,100%{opacity:1} 50%{opacity:0.5} }
        ::-webkit-scrollbar { width:4px }
        ::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.2); border-radius:2px }
        .nav-item:hover { background:rgba(255,255,255,0.1) !important; transform:translateX(4px); }
        .nav-item { transition:all 0.2s ease !important; }
        .btn:hover { opacity:0.85; transform:translateY(-1px); }
        .btn { transition:all 0.2s ease; cursor:pointer; border:none; }
        .row-hover:hover { background:rgba(255,255,255,0.05) !important; }
        input::placeholder { color:rgba(255,255,255,0.3) }
        input { caret-color:#667EEA }
      `}</style>

      <Notif notif={notif} />

      <div style={{ display:"flex", minHeight:"100vh" }}>

        {/* ── SIDEBAR ── */}
        <div style={{ width:240, background:"rgba(0,0,0,0.3)", backdropFilter:"blur(20px)", borderRight:"1px solid rgba(255,255,255,0.08)", padding:"32px 16px", display:"flex", flexDirection:"column", gap:4, position:"sticky", top:0, height:"100vh" }}>
          <div style={{ padding:"0 12px 32px" }}>
            <div style={{ fontSize:22, fontWeight:800, fontFamily:"'Syne',sans-serif", background:"linear-gradient(135deg,#667EEA,#F093FB)", WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent" }}>👁️ AttendAI</div>
            <div style={{ fontSize:11, color:"rgba(255,255,255,0.4)", marginTop:4 }}>Smart Classroom System</div>
          </div>

          {navItems.map(item => (
            <div key={item.id} className="nav-item" onClick={() => { setPage(item.id); setSearch(""); }} style={{ padding:"12px 16px", borderRadius:12, cursor:"pointer", display:"flex", alignItems:"center", gap:12, background: page===item.id ? "linear-gradient(135deg,rgba(102,126,234,0.3),rgba(240,147,251,0.3))" : "transparent", borderLeft: page===item.id ? "3px solid #667EEA" : "3px solid transparent", color: page===item.id ? "#fff" : "rgba(255,255,255,0.55)", fontWeight: page===item.id ? 600 : 400, fontSize:14 }}>
              <span style={{ fontSize:18 }}>{item.icon}</span>{item.label}
            </div>
          ))}

          {/* Flask status */}
          <div style={{ marginTop:"auto", padding:"16px 12px" }}>
            <div style={{ background:"rgba(102,126,234,0.15)", border:"1px solid rgba(102,126,234,0.3)", borderRadius:12, padding:14 }}>
              <div style={{ fontSize:11, color:"rgba(255,255,255,0.4)", marginBottom:6 }}>Flask API Status</div>
              <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                <div style={{ width:8, height:8, borderRadius:"50%", background: todayData ? "#38ef7d" : "#FF416C", animation:"pulse 2s infinite" }} />
                <span style={{ fontSize:12, color: todayData ? "#38ef7d" : "#FF416C", fontWeight:600 }}>
                  {todayData ? "Connected ✅" : "Disconnected ❌"}
                </span>
              </div>
              {!todayData && <div style={{ fontSize:10, color:"rgba(255,255,255,0.3)", marginTop:6 }}>Run: python app.py</div>}
            </div>
          </div>
        </div>

        {/* ── MAIN ── */}
        <div style={{ flex:1, padding:"40px", overflowY:"auto" }}>

          {/* ══ DASHBOARD ══ */}
          {page==="dashboard" && (
            <div style={{ animation:"fadeIn 0.4s ease" }}>
              <h1 style={{ fontSize:36, fontWeight:800, fontFamily:"'Syne',sans-serif", background:"linear-gradient(135deg,#fff,rgba(255,255,255,0.6))", WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent", marginBottom:8 }}>Good Morning! 👋</h1>
              <p style={{ color:"rgba(255,255,255,0.5)", marginBottom:36, fontSize:15 }}>Live attendance overview for {new Date().toLocaleDateString("en-IN",{weekday:"long",day:"numeric",month:"long"})}</p>

              {/* Stats */}
              <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:20, marginBottom:36 }}>
                <StatCard label="Total Students"   value={students.length}                          icon="👥" color="#667EEA" delay={0}   />
                <StatCard label="Present Today"    value={todayData?.present_count ?? "—"}          icon="✅" color="#38ef7d" delay={0.1} />
                <StatCard label="Absent Today"     value={todayData?.absent_count  ?? "—"}          icon="❌" color="#FF416C" delay={0.2} />
                <StatCard label="Attendance Rate"  value={todayData ? `${todayData.percentage}%`:"—"} icon="📊" color="#FFC837" delay={0.3} />
              </div>

              {/* Progress */}
              {todayData && (
                <div style={{ background:"rgba(255,255,255,0.07)", backdropFilter:"blur(20px)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:20, padding:28, animation:"slideUp 0.6s ease 0.4s both" }}>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
                    <div style={{ fontWeight:700, fontSize:16, fontFamily:"'Syne',sans-serif" }}>Today — {todayData.date}</div>
                    <div style={{ background: todayData.percentage>=75?"rgba(56,239,125,0.15)":"rgba(255,65,108,0.15)", color: todayData.percentage>=75?"#38ef7d":"#FF416C", padding:"4px 14px", borderRadius:20, fontSize:13, fontWeight:600 }}>
                      {todayData.percentage>=75?"✅ Good":"⚠️ Low"}
                    </div>
                  </div>
                  <div style={{ background:"rgba(255,255,255,0.1)", borderRadius:50, height:10, marginBottom:24 }}>
                    <div style={{ width:`${todayData.percentage}%`, height:"100%", borderRadius:50, background:"linear-gradient(90deg,#667EEA,#38ef7d)", boxShadow:"0 0 20px rgba(102,126,234,0.5)", transition:"width 1s ease" }} />
                  </div>
                  <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
                    {todayData.records.map((r,i) => (
                      <div key={i} style={{ display:"flex", alignItems:"center", gap:14, padding:"10px 14px", borderRadius:12, background: r.Status==="Present"?"rgba(56,239,125,0.08)":"rgba(255,65,108,0.08)", border:`1px solid ${r.Status==="Present"?"rgba(56,239,125,0.2)":"rgba(255,65,108,0.2)"}` }}>
                        <Avatar name={r.Name} size={34} />
                        <div style={{ flex:1, fontSize:14, fontWeight:500 }}>{r.Name}</div>
                        <div style={{ fontSize:12, color:"rgba(255,255,255,0.4)" }}>{r.Time}</div>
                        <div style={{ padding:"3px 12px", borderRadius:20, fontSize:12, fontWeight:600, background: r.Status==="Present"?"rgba(56,239,125,0.2)":"rgba(255,65,108,0.2)", color: r.Status==="Present"?"#38ef7d":"#FF416C" }}>
                          {r.Status==="Present"?"✅ Present":"❌ Absent"}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {!todayData && (
                <div style={{ textAlign:"center", padding:60, background:"rgba(255,255,255,0.04)", borderRadius:20, border:"1px dashed rgba(255,255,255,0.15)" }}>
                  <div style={{ fontSize:40, marginBottom:16 }}>🔌</div>
                  <div style={{ fontWeight:700, fontSize:18, marginBottom:8 }}>Flask Server Not Running</div>
                  <div style={{ color:"rgba(255,255,255,0.4)", fontSize:14, marginBottom:20 }}>Start the backend to see live data</div>
                  <div style={{ background:"rgba(0,0,0,0.3)", borderRadius:12, padding:"14px 24px", display:"inline-block", fontFamily:"monospace", fontSize:14, color:"#667EEA" }}>
                    python app.py
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ══ ATTENDANCE ══ */}
          {page==="attendance" && (
            <div style={{ animation:"fadeIn 0.4s ease" }}>
              <h1 style={{ fontSize:32, fontWeight:800, fontFamily:"'Syne',sans-serif", marginBottom:8 }}>📋 Attendance Records</h1>
              <p style={{ color:"rgba(255,255,255,0.5)", marginBottom:32 }}>View daily attendance from your CSV files</p>

              {/* Date buttons */}
              <div style={{ display:"flex", gap:10, marginBottom:24, flexWrap:"wrap" }}>
                {allDates.map(d => (
                  <button key={d} className="btn" onClick={() => { setSelDate(d); loadDateData(d); }} style={{ padding:"10px 20px", borderRadius:12, fontSize:13, fontWeight:600, background: selDate===d ? "linear-gradient(135deg,#667EEA,#F093FB)" : "rgba(255,255,255,0.08)", color:"#fff", border: selDate===d ? "none" : "1px solid rgba(255,255,255,0.12)" }}>
                    📅 {d}
                  </button>
                ))}
                {allDates.length === 0 && <div style={{ color:"rgba(255,255,255,0.4)", fontSize:14 }}>No records yet — run the attendance camera first!</div>}
              </div>

              {/* Search */}
              <div style={{ position:"relative", marginBottom:24 }}>
                <span style={{ position:"absolute", left:16, top:"50%", transform:"translateY(-50%)" }}>🔍</span>
                <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search student..." style={{ width:"100%", padding:"14px 16px 14px 44px", background:"rgba(255,255,255,0.07)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:14, color:"#fff", fontSize:14, outline:"none" }} />
              </div>

              {loading.date ? <Spinner /> : dateData && (
                <>
                  {/* Summary */}
                  <div style={{ display:"flex", gap:12, marginBottom:20 }}>
                    {[{label:"Total",value:dateData.total,color:"#667EEA"},{label:"Present",value:dateData.present_count,color:"#38ef7d"},{label:"Absent",value:dateData.absent_count,color:"#FF416C"},{label:"Rate",value:`${dateData.percentage}%`,color:"#FFC837"}].map(s=>(
                      <div key={s.label} style={{ flex:1, padding:"16px 20px", borderRadius:14, background:"rgba(255,255,255,0.05)", border:`1px solid ${s.color}33`, display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                        <span style={{ color:"rgba(255,255,255,0.5)", fontSize:13 }}>{s.label}</span>
                        <span style={{ color:s.color, fontWeight:800, fontSize:22, fontFamily:"'Syne',sans-serif" }}>{s.value}</span>
                      </div>
                    ))}
                  </div>

                  {/* Table */}
                  <div style={{ background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:20, overflow:"hidden" }}>
                    <div style={{ display:"grid", gridTemplateColumns:"2fr 1fr 1fr 1fr", padding:"16px 24px", background:"rgba(102,126,234,0.15)", borderBottom:"1px solid rgba(255,255,255,0.08)", fontSize:12, fontWeight:700, color:"rgba(255,255,255,0.5)", textTransform:"uppercase", letterSpacing:1 }}>
                      <div>Student</div><div>Date</div><div>Time</div><div>Status</div>
                    </div>
                    {filtRecords.map((r,i) => (
                      <div key={i} className="row-hover" style={{ display:"grid", gridTemplateColumns:"2fr 1fr 1fr 1fr", padding:"14px 24px", alignItems:"center", borderBottom:"1px solid rgba(255,255,255,0.04)", transition:"all 0.2s" }}>
                        <div style={{ display:"flex", alignItems:"center", gap:12 }}><Avatar name={r.Name} size={34}/><span style={{ fontWeight:500, fontSize:14 }}>{r.Name}</span></div>
                        <div style={{ color:"rgba(255,255,255,0.5)", fontSize:13 }}>{r.Date}</div>
                        <div style={{ color:"rgba(255,255,255,0.5)", fontSize:13 }}>{r.Time}</div>
                        <div style={{ display:"inline-flex", padding:"4px 14px", borderRadius:20, fontSize:12, fontWeight:600, width:"fit-content", background: r.Status==="Present"?"rgba(56,239,125,0.15)":"rgba(255,65,108,0.15)", color: r.Status==="Present"?"#38ef7d":"#FF416C" }}>
                          {r.Status==="Present"?"✅ Present":"❌ Absent"}
                        </div>
                      </div>
                    ))}
                    {filtRecords.length===0 && <div style={{ padding:40, textAlign:"center", color:"rgba(255,255,255,0.3)" }}>No records found</div>}
                  </div>
                </>
              )}
            </div>
          )}

          {/* ══ STUDENTS ══ */}
          {page==="students" && (
            <div style={{ animation:"fadeIn 0.4s ease" }}>
              <h1 style={{ fontSize:32, fontWeight:800, fontFamily:"'Syne',sans-serif", marginBottom:8 }}>👥 Students</h1>
              <p style={{ color:"rgba(255,255,255,0.5)", marginBottom:32 }}>{students.length} students registered in system</p>

              <div style={{ position:"relative", marginBottom:28 }}>
                <span style={{ position:"absolute", left:16, top:"50%", transform:"translateY(-50%)" }}>🔍</span>
                <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search student..." style={{ width:"100%", padding:"14px 16px 14px 44px", background:"rgba(255,255,255,0.07)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:14, color:"#fff", fontSize:14, outline:"none" }} />
              </div>

              {loading.students ? <Spinner /> : (
                <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:20 }}>
                  {filtStudents.map((s,i) => (
                    <div key={s.name} style={{ background:"rgba(255,255,255,0.07)", backdropFilter:"blur(20px)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:20, padding:24, animation:`slideUp 0.5s ease ${i*0.08}s both`, transition:"all 0.3s" }}>
                      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:20 }}>
                        <div style={{ display:"flex", alignItems:"center", gap:12 }}>
                          <Avatar name={s.name} size={46} />
                          <div>
                            <div style={{ fontWeight:700, fontSize:15 }}>{s.name}</div>
                            <div style={{ color:"rgba(255,255,255,0.4)", fontSize:11, marginTop:2 }}>Since {s.registered}</div>
                          </div>
                        </div>
                        <button className="btn" onClick={() => handleDeleteStudent(s.name)} style={{ background:"rgba(255,65,108,0.15)", border:"1px solid rgba(255,65,108,0.3)", color:"#FF416C", padding:"6px 10px", borderRadius:8, fontSize:13 }}>🗑️</button>
                      </div>
                      <div style={{ background:"rgba(56,239,125,0.1)", border:"1px solid rgba(56,239,125,0.2)", borderRadius:12, padding:"10px 16px", textAlign:"center" }}>
                        <div style={{ color:"#38ef7d", fontWeight:700, fontSize:13 }}>✅ Registered</div>
                      </div>
                    </div>
                  ))}
                  {filtStudents.length===0 && (
                    <div style={{ gridColumn:"1/-1", textAlign:"center", padding:60, color:"rgba(255,255,255,0.3)" }}>
                      <div style={{ fontSize:40, marginBottom:12 }}>👥</div>
                      No students found. Go to Register page to add students!
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ══ REGISTER ══ */}
          {page==="register" && (
            <div style={{ animation:"fadeIn 0.4s ease", maxWidth:520 }}>
              <h1 style={{ fontSize:32, fontWeight:800, fontFamily:"'Syne',sans-serif", marginBottom:8 }}>➕ Register Student</h1>
              <p style={{ color:"rgba(255,255,255,0.5)", marginBottom:40 }}>Add a new student face to the system</p>

              <div style={{ background:"rgba(255,255,255,0.07)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:24, padding:36 }}>
                {/* Avatar preview */}
                <div style={{ display:"flex", justifyContent:"center", marginBottom:32 }}>
                  {regName ? <Avatar name={regName} size={80} /> : (
                    <div style={{ width:80, height:80, borderRadius:"50%", background:"rgba(255,255,255,0.08)", border:"2px dashed rgba(255,255,255,0.2)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:28 }}>👤</div>
                  )}
                </div>

                {/* Input */}
                <label style={{ fontSize:13, fontWeight:600, color:"rgba(255,255,255,0.6)", display:"block", marginBottom:8 }}>Student Full Name</label>
                <input value={regName} onChange={e=>setRegName(e.target.value)} onKeyDown={e=>e.key==="Enter"&&handleRegister()} placeholder="e.g. Dhanish Kumar" style={{ width:"100%", padding:"14px 18px", background:"rgba(255,255,255,0.08)", border:"1px solid rgba(255,255,255,0.15)", borderRadius:14, color:"#fff", fontSize:15, outline:"none", marginBottom:24 }} />

                {/* How it works */}
                <div style={{ background:"rgba(102,126,234,0.1)", border:"1px solid rgba(102,126,234,0.25)", borderRadius:14, padding:18, marginBottom:28 }}>
                  <div style={{ fontSize:13, fontWeight:700, color:"#667EEA", marginBottom:10 }}>📋 What Happens Next</div>
                  {["Enter student name above","Click 'Open Camera' button","Camera window opens on screen","Align face in green box → Press SPACE","Photo saved automatically!"].map((s,i)=>(
                    <div key={i} style={{ display:"flex", gap:10, marginBottom:6, fontSize:13, color:"rgba(255,255,255,0.6)" }}>
                      <span style={{ color:"#667EEA", fontWeight:700 }}>{i+1}.</span>{s}
                    </div>
                  ))}
                </div>

                {/* Buttons */}
                <div style={{ display:"flex", gap:12 }}>
                  <button className="btn" onClick={handleRegister} disabled={loading.register} style={{ flex:1, padding:"15px 0", borderRadius:14, background: loading.register ? "rgba(255,255,255,0.1)" : "linear-gradient(135deg,#667EEA,#F093FB)", color:"#fff", fontWeight:700, fontSize:15 }}>
                    {loading.register ? "⏳ Opening Camera..." : "📷 Open Camera"}
                  </button>
                  <button className="btn" onClick={()=>setRegName("")} style={{ padding:"15px 18px", borderRadius:14, background:"rgba(255,255,255,0.08)", color:"rgba(255,255,255,0.6)", border:"1px solid rgba(255,255,255,0.12)" }}>🗑️</button>
                </div>
              </div>
            </div>
          )}

          {/* ══ CAMERA ══ */}
          {page==="camera" && (
            <div style={{ animation:"fadeIn 0.4s ease" }}>
              <h1 style={{ fontSize:32, fontWeight:800, fontFamily:"'Syne',sans-serif", marginBottom:8 }}>📷 Attendance Camera</h1>
              <p style={{ color:"rgba(255,255,255,0.5)", marginBottom:32 }}>Live face recognition with anti-spoofing</p>

              <div style={{ display:"grid", gridTemplateColumns:"1.5fr 1fr", gap:24 }}>
                {/* Video feed */}
                <div style={{ background:"rgba(0,0,0,0.4)", borderRadius:20, overflow:"hidden", border:"1px solid rgba(255,255,255,0.1)", aspectRatio:"4/3", display:"flex", alignItems:"center", justifyContent:"center", position:"relative" }}>
                  {camStatus.active ? (
                    <img src="http://localhost:5000/api/video-feed" alt="Live feed" style={{ width:"100%", height:"100%", objectFit:"cover" }} crossOrigin="anonymous"/>
                  ) : (
                    <div style={{ textAlign:"center" }}>
                      <div style={{ fontSize:56, opacity:0.2 }}>📷</div>
                      <div style={{ color:"rgba(255,255,255,0.3)", marginTop:12, fontSize:14 }}>Camera not started</div>
                    </div>
                  )}

                  {/* Live badge */}
                  {camStatus.active && (
                    <div style={{ position:"absolute", top:16, left:16, background:"rgba(255,65,108,0.9)", padding:"4px 12px", borderRadius:20, fontSize:12, fontWeight:700, display:"flex", alignItems:"center", gap:6 }}>
                      <div style={{ width:6, height:6, borderRadius:"50%", background:"#fff", animation:"pulse 1s infinite" }} />
                      LIVE
                    </div>
                  )}
                </div>

                {/* Controls */}
                <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
                  {/* Status card */}
                  <div style={{ background:"rgba(255,255,255,0.07)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:20, padding:24 }}>
                    <div style={{ fontSize:13, color:"rgba(255,255,255,0.5)", marginBottom:8 }}>System Status</div>
                    <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:16 }}>
                      <div style={{ width:10, height:10, borderRadius:"50%", background: camStatus.active?"#38ef7d":"rgba(255,255,255,0.3)", animation: camStatus.active?"pulse 1.5s infinite":"none" }} />
                      <span style={{ fontWeight:700, color: camStatus.active?"#38ef7d":"rgba(255,255,255,0.5)" }}>
                        {camStatus.active ? "ACTIVE" : "INACTIVE"}
                      </span>
                    </div>
                    {camStatus.message && (
                      <div style={{ background:"rgba(102,126,234,0.1)", border:"1px solid rgba(102,126,234,0.2)", borderRadius:12, padding:12, fontSize:13, color:"rgba(255,255,255,0.7)" }}>
                        💬 {camStatus.message}
                      </div>
                    )}
                  </div>

                  {/* How it works */}
                  <div style={{ background:"rgba(255,255,255,0.07)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:20, padding:24 }}>
                    <div style={{ fontSize:13, fontWeight:700, color:"rgba(255,255,255,0.6)", marginBottom:14 }}>HOW IT WORKS</div>
                    {[{icon:"👁️",text:"Blink to verify you're real",color:"#667EEA"},{icon:"🔍",text:"Face recognition runs",color:"#F093FB"},{icon:"✅",text:"Attendance auto-saved to CSV",color:"#38ef7d"}].map((s,i)=>(
                      <div key={i} style={{ display:"flex", gap:12, alignItems:"center", marginBottom:12 }}>
                        <div style={{ width:32, height:32, borderRadius:"50%", background:`${s.color}22`, display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0 }}>{s.icon}</div>
                        <span style={{ fontSize:13, color:"rgba(255,255,255,0.6)" }}>{s.text}</span>
                      </div>
                    ))}
                  </div>

                  {/* Start/Stop button */}
                  <button className="btn" onClick={camStatus.active ? handleStopCamera : handleStartCamera} disabled={loading.camera} style={{ padding:"18px 0", borderRadius:16, background: camStatus.active ? "linear-gradient(135deg,#FF416C,#FF4B2B)" : "linear-gradient(135deg,#11998e,#38ef7d)", color:"#fff", fontWeight:700, fontSize:16, boxShadow: camStatus.active ? "0 8px 30px rgba(255,65,108,0.4)" : "0 8px 30px rgba(56,239,125,0.4)" }}>
                    {loading.camera ? "⏳ Starting..." : camStatus.active ? "⏹️ Stop Camera" : "▶️ Start Attendance"}
                  </button>
                </div>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
