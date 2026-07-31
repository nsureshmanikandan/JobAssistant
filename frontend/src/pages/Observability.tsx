import { useEffect, useState } from "react";
import { CheckCircle2, XCircle, Inbox } from "lucide-react";
import { api } from "../api/client";
import type { LLMCallLogEntry } from "../types";

export default function Observability() {
  const [calls, setCalls] = useState<LLMCallLogEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listLlmCalls().then(setCalls).finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-indigo-950 tracking-tight">LLM Call Log</h1>
        <p className="text-sm text-slate-500 mt-0.5">Every scoring and tailoring call — provider, latency, and outcome.</p>
      </div>

      {!loading && calls.length === 0 ? (
        <div className="flex flex-col items-center text-center gap-3 bg-white border border-dashed border-slate-300 rounded-xl py-14">
          <div className="h-12 w-12 rounded-full bg-indigo-50 flex items-center justify-center">
            <Inbox className="h-6 w-6 text-indigo-400" />
          </div>
          <p className="font-medium text-indigo-950">No LLM calls logged yet</p>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">
              <tr>
                <th className="px-4 py-3">Time</th>
                <th className="px-4 py-3">Provider / Model</th>
                <th className="px-4 py-3">Prompt</th>
                <th className="px-4 py-3">Latency</th>
                <th className="px-4 py-3">Result</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {calls.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50/60">
                  <td className="px-4 py-3 text-slate-600 whitespace-nowrap">{new Date(c.created_at).toLocaleString()}</td>
                  <td className="px-4 py-3 font-medium text-indigo-950">{c.provider} / {c.model}</td>
                  <td className="px-4 py-3">
                    <span className="bg-indigo-50 text-indigo-700 text-xs font-medium px-2 py-1 rounded-full">
                      {c.prompt_id}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600 tabular-nums">{c.latency_ms}ms</td>
                  <td className="px-4 py-3">
                    {c.success ? (
                      <span className="inline-flex items-center gap-1 text-emerald-700">
                        <CheckCircle2 className="h-4 w-4" /> Success
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-red-700">
                        <XCircle className="h-4 w-4" /> Failed
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
