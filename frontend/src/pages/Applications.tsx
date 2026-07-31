import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Application } from "../types";

const STATUSES = ["approved", "applied", "skipped"];

export default function Applications() {
  const [applications, setApplications] = useState<Application[]>([]);

  useEffect(() => {
    api.listApplications().then(setApplications);
  }, []);

  const handleStatusChange = async (id: number, status: string) => {
    const updated = await api.updateApplicationStatus(id, status);
    setApplications((prev) => prev.map((a) => (a.id === id ? updated : a)));
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-slate-900">Application History</h1>
      <table className="w-full text-sm bg-white border border-slate-200 rounded-lg overflow-hidden">
        <thead className="bg-slate-100 text-left">
          <tr>
            <th className="p-2">Job ID</th>
            <th className="p-2">Status</th>
            <th className="p-2">Applied At</th>
          </tr>
        </thead>
        <tbody>
          {applications.map((application) => (
            <tr key={application.id} className="border-t border-slate-100">
              <td className="p-2">{application.job_id}</td>
              <td className="p-2">
                <select
                  className="border border-slate-300 rounded p-1"
                  value={application.status}
                  onChange={(e) => handleStatusChange(application.id, e.target.value)}
                >
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </td>
              <td className="p-2">{application.applied_at ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
