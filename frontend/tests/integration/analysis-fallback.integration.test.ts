import { beforeEach, describe, expect, it, vi } from "vitest";

const { postMock } = vi.hoisted(() => ({
  postMock: vi.fn()
}));

vi.mock("@/services/api", () => ({
  api: {
    post: postMock,
    get: vi.fn()
  }
}));

import { analyzeResumeWithFallback } from "@/services/analysis-service";

describe("analyzeResumeWithFallback", () => {
  beforeEach(() => {
    postMock.mockReset();
  });

  it("falls back to v1 endpoint when v2 route is unavailable", async () => {
    postMock
      .mockRejectedValueOnce({ isAxiosError: true, response: { status: 404 } })
      .mockResolvedValueOnce({ data: { matchScore: 77, strengths: [], skillGaps: [], transferableSkills: [], roadmap: [], certifications: [] } });

    const formData = new FormData();
    formData.append("resume", new Blob(["x"], { type: "application/pdf" }), "resume.pdf");

    const result = await analyzeResumeWithFallback(formData);

    expect(postMock).toHaveBeenCalledTimes(2);
    expect(postMock.mock.calls[0][0]).toBe("/resume/analyze/v2");
    expect(postMock.mock.calls[1][0]).toBe("/resume/analyze");
    expect(result.matchScore).toBe(77);
  });
});
