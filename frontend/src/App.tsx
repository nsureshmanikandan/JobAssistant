import { Routes, Route, NavLink } from "react-router-dom";
import { LayoutDashboard, FilePlus2, Briefcase, Settings as SettingsIcon, Activity, Sparkles } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import JobReview from "./pages/JobReview";
import ManualPaste from "./pages/ManualPaste";
import Applications from "./pages/Applications";
import Settings from "./pages/Settings";
import Observability from "./pages/Observability";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/manual", label: "Add Job", icon: FilePlus2, end: false },
  { to: "/applications", label: "Applications", icon: Briefcase, end: false },
  { to: "/settings", label: "Settings", icon: SettingsIcon, end: false },
  { to: "/observability", label: "Observability", icon: Activity, end: false },
];

export default function App() {
  return (
    <div className="min-h-dvh flex bg-violet-50">
      <aside className="w-64 shrink-0 bg-indigo-950 text-indigo-100 flex flex-col">
        <div className="flex items-center gap-2 px-6 py-5 border-b border-white/10">
          <div className="h-8 w-8 rounded-lg bg-indigo-500 flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-white" strokeWidth={2.5} />
          </div>
          <span className="font-bold text-white tracking-tight">Job Assistant</span>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150 ${
                  isActive
                    ? "bg-indigo-500 text-white shadow-sm"
                    : "text-indigo-200 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              <Icon className="h-[18px] w-[18px]" strokeWidth={2} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-6 py-4 border-t border-white/10 text-xs text-indigo-300">
          Chennai · GenAI / Agentic AI roles
        </div>
      </aside>

      <main className="flex-1 min-w-0 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-8 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/jobs/:id" element={<JobReview />} />
            <Route path="/manual" element={<ManualPaste />} />
            <Route path="/applications" element={<Applications />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/observability" element={<Observability />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
