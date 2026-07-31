// Mirrors the section-header heuristic used server-side for PDF export
// (backend/app/services/export.py::_is_section_header) so the on-screen
// preview looks like the PDF the user will actually download.
function isSectionHeader(line: string): boolean {
  const trimmed = line.trim();
  return trimmed.length > 1 && trimmed === trimmed.toUpperCase() && /[A-Z]/.test(trimmed);
}

function isBullet(line: string): boolean {
  return /^\s*[-•]/.test(line);
}

function isContactLine(line: string): boolean {
  return line.includes("|") && !isBullet(line);
}

export default function ResumePreview({ content }: { content: string }) {
  if (!content.trim()) {
    return <p className="text-slate-400 text-sm italic">Nothing to preview yet.</p>;
  }

  const lines = content.split("\n");
  const firstNonBlankIndex = lines.findIndex((l) => l.trim() !== "");

  return (
    <div className="space-y-1">
      {lines.map((line, i) => {
        if (line.trim() === "") return <div key={i} className="h-3" />;

        // First non-blank line is treated as the candidate's name, regardless
        // of case, and gets the large centered treatment real resumes use.
        if (i === firstNonBlankIndex) {
          return (
            <h1 key={i} className="text-xl font-bold text-indigo-950 text-center mb-1">
              {line.trim()}
            </h1>
          );
        }
        if (isContactLine(line)) {
          return (
            <p key={i} className="text-xs text-slate-500 text-center mb-3">
              {line.trim()}
            </p>
          );
        }
        if (isSectionHeader(line)) {
          return (
            <h3
              key={i}
              className="text-sm font-bold text-indigo-950 uppercase tracking-wide pt-3 pb-1 border-b border-indigo-100"
            >
              {line.trim()}
            </h3>
          );
        }
        if (isBullet(line)) {
          return (
            <p key={i} className="text-sm text-slate-700 leading-relaxed pl-4 relative">
              <span className="absolute left-0 text-indigo-400">•</span>
              {line.replace(/^\s*[-•]\s*/, "")}
            </p>
          );
        }
        return (
          <p key={i} className="text-sm text-slate-700 leading-relaxed">
            {line}
          </p>
        );
      })}
    </div>
  );
}
