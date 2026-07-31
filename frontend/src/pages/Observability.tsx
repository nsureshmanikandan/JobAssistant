import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { LLMCallLogEntry } from "../types";

export default function Observability() {
  const [calls, setCalls] = useState<LLMCallLogEntry[]>([]);

  useEffect(() => {
    api.listLlmCalls().then(setCalls);
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-slate-900">LLM Call Log</h1>
      <table className="w-full text-sm bg-white border border-slate-200 rounded-lg overflow-hidden">
        <thead className="bg-slate-100 text-left">
          <tr>
            <th className="p-2">Time</th>
            <th className="p-2">Provider</th>
            <th className="p-2">Prompt</th>
            <th className="p-2">Latency</th>
            <th className="p-2">Success</th>
          </tr>
        </thead>
        <tbody>
          {calls.map((c) => (
            <tr key={c.id} className="border-t border-slate-100">
              <td className="p-2">{new Date(c.created_at).toLocaleString()}</td>
              <td className="p-2">{c.provider} / {c.model}</td>
              <td className="p-2">{c.prompt_id}</td>
              <td className="p-2">{c.latency_ms}ms</td>
              <td className="p-2">{c.success ? "✓" : "✗"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
