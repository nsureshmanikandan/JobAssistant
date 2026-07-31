import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi, describe, it, expect } from "vitest";
import Dashboard from "../Dashboard";
import { api } from "../../api/client";

vi.mock("../../api/client", () => ({
  api: { listJobs: vi.fn() },
}));

describe("Dashboard", () => {
  it("renders jobs returned by the API", async () => {
    (api.listJobs as any).mockResolvedValue([
      {
        id: 1,
        title: "GenAI Architect",
        company: "Acme",
        location: "Chennai",
        match_percentage: 92,
        sponsorship_required: false,
        source_site: "linkedin",
        status: "pending_review",
        needs_manual_paste: false,
      },
    ]);
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText("GenAI Architect")).toBeInTheDocument());
    expect(screen.getByText(/92%/)).toBeInTheDocument();
  });
});
