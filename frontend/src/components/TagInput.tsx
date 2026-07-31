import { useState, KeyboardEvent } from "react";
import { X } from "lucide-react";

interface TagInputProps {
  value: string; // comma-separated, e.g. "GenAI Architect,Agentic AI Architect"
  onChange: (value: string) => void;
  placeholder?: string;
}

// Job-portal-style chip input (like Naukri's "Preferred Job Role" / "Preferred
// Work Locations" pickers) instead of a raw comma-separated text field.
export default function TagInput({ value, onChange, placeholder }: TagInputProps) {
  const tags = value.split(",").map((t) => t.trim()).filter(Boolean);
  const [draft, setDraft] = useState("");

  const commit = () => {
    const trimmed = draft.trim();
    if (trimmed && !tags.includes(trimmed)) {
      onChange([...tags, trimmed].join(","));
    }
    setDraft("");
  };

  const removeTag = (tag: string) => {
    onChange(tags.filter((t) => t !== tag).join(","));
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      commit();
    } else if (e.key === "Backspace" && draft === "" && tags.length > 0) {
      removeTag(tags[tags.length - 1]);
    }
  };

  return (
    <div className="border border-slate-300 rounded-lg px-2 py-1.5 flex flex-wrap gap-1.5 items-center focus-within:ring-2 focus-within:ring-indigo-500 focus-within:border-indigo-500">
      {tags.map((tag) => (
        <span
          key={tag}
          className="inline-flex items-center gap-1 bg-indigo-50 text-indigo-700 text-sm font-medium pl-2.5 pr-1.5 py-1 rounded-full"
        >
          {tag}
          <button
            type="button"
            onClick={() => removeTag(tag)}
            className="hover:bg-indigo-100 rounded-full p-0.5 cursor-pointer"
            aria-label={`Remove ${tag}`}
          >
            <X className="h-3 w-3" />
          </button>
        </span>
      ))}
      <input
        className="flex-1 min-w-[140px] text-sm outline-none py-1 bg-transparent"
        value={draft}
        placeholder={tags.length === 0 ? placeholder : "Add another..."}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={commit}
      />
    </div>
  );
}
