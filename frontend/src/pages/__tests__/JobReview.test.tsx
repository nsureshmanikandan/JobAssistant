import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi, describe, it, expect } from "vitest";
import JobReview from "../JobReview";
import { api } from "../../api/client";

vi.mock("../../api/client", () => ({
  api: {
    getJob: vi.fn(),
    tailorJob: vi.fn(),
    approveJob: vi.fn(),
    rejectJob: vi.fn(),
    resumePdfUrl: (id: number) => `http://localhost:8000/jobs/${id}/resume.pdf`,
    coverLetterPdfUrl: (id: number) => `http://localhost:8000/jobs/${id}/cover-letter.pdf`,
  },
}));

const baseJob = {
  id: 1,
  title: "GenAI Architect",
  company: "Acme",
  location: "Chennai",
  description: "We need a GenAI Architect...",
  match_percentage: 92,
  sponsorship_required: false,
  status: "pending_review",
  tailored_resume: null,
  tailored_cover_letter: null,
};

describe("JobReview", () => {
  it("generates tailored materials and shows download links once available", async () => {
    (api.getJob as any).mockResolvedValue(baseJob);
    (api.tailorJob as any).mockResolvedValue({
      ...baseJob,
      tailored_resume: "SUMMARY\n...",
      tailored_cover_letter: "Dear Hiring Manager,\n...",
    });

    render(
      <MemoryRouter initialEntries={["/jobs/1"]}>
        <Routes>
          <Route path="/jobs/:id" element={<JobReview />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText("GenAI Architect")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /generate tailored resume/i }));

    await waitFor(() => expect(screen.getByText(/download resume pdf/i)).toBeInTheDocument());
    expect(screen.getByText(/download cover letter pdf/i)).toBeInTheDocument();
  });
});
