import { Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import JobReview from "./pages/JobReview";
import ManualPaste from "./pages/ManualPaste";
import Applications from "./pages/Applications";
import Settings from "./pages/Settings";
import Observability from "./pages/Observability";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `px-3 py-2 rounded-md text-sm font-medium ${
    isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
  }`;

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200 px-6 py-3 flex gap-2">
        <NavLink to="/" className={navLinkClass} end>Dashboard</NavLink>
        <NavLink to="/manual" className={navLinkClass}>Add Job</NavLink>
        <NavLink to="/applications" className={navLinkClass}>Applications</NavLink>
        <NavLink to="/settings" className={navLinkClass}>Settings</NavLink>
        <NavLink to="/observability" className={navLinkClass}>Observability</NavLink>
      </nav>
      <main className="max-w-5xl mx-auto p-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/jobs/:id" element={<JobReview />} />
          <Route path="/manual" element={<ManualPaste />} />
          <Route path="/applications" element={<Applications />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/observability" element={<Observability />} />
        </Routes>
      </main>
    </div>
  );
}
