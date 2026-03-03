import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { pushMock, analyzeMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  analyzeMock: vi.fn()
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock
  })
}));

vi.mock("@/services/analysis-service", () => ({
  analyzeResumeWithFallback: analyzeMock,
  fetchServicesHealth: vi.fn().mockResolvedValue({
    status: "ok",
    backend: { status: "ok" },
    ml: { status: "ok" }
  })
}));

vi.mock("@/components/navbar", () => ({ Navbar: () => <div /> }));
vi.mock("@/components/match-score-ring", () => ({ MatchScoreRing: () => <div /> }));
vi.mock("@/components/dashboard-charts", () => ({ DashboardCharts: () => <div /> }));
vi.mock("@/components/advanced-score-analytics", () => ({ AdvancedScoreAnalytics: () => <div /> }));
vi.mock("@/components/skill-gap-accordion", () => ({ SkillGapAccordion: () => <div /> }));
vi.mock("@/components/roadmap-timeline", () => ({ RoadmapTimeline: () => <div /> }));
vi.mock("@/components/resume-rewrite-panel", () => ({ ResumeRewritePanel: () => <div /> }));
vi.mock("@/components/ats-compatibility-card", () => ({ AtsCompatibilityCard: () => <div /> }));
vi.mock("@/components/floating-particles", () => ({ FloatingParticles: () => <div /> }));
vi.mock("@/components/ui/card", () => ({ Card: ({ children }: { children: ReactNode }) => <div>{children}</div> }));
vi.mock("@/components/ui/button", () => ({
  Button: ({ children, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) => <button {...props}>{children}</button>
}));
vi.mock("@/components/upload-zone", () => ({
  UploadZone: ({ onSelectFile }: { onSelectFile: (file: File) => void }) => (
    <button onClick={() => onSelectFile(new File(["resume"], "resume.pdf", { type: "application/pdf" }))}>Select File</button>
  )
}));

import DashboardPage from "@/app/dashboard/page";

describe("dashboard auth expired flow", () => {
  beforeEach(() => {
    pushMock.mockReset();
    analyzeMock.mockReset();
    localStorage.clear();
  });

  it("redirects to login and clears token on 401", async () => {
    localStorage.setItem("resume-analyzer-token", "abc123");
    analyzeMock.mockRejectedValue({
      isAxiosError: true,
      response: { status: 401 }
    });

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });

    render(
      <QueryClientProvider client={queryClient}>
        <DashboardPage />
      </QueryClientProvider>
    );

    fireEvent.click(screen.getByText("Select File"));
    fireEvent.click(screen.getByText("Analyze Resume"));

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/login");
    });

    expect(localStorage.getItem("resume-analyzer-token")).toBeNull();
  });
});
