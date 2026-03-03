import { describe, expect, it } from "vitest";
import { getAnalysisErrorInfo } from "@/utils/analysis-errors";

describe("analysis error mapping", () => {
  it("returns friendly unreadable-PDF guidance", () => {
    const error = {
      isAxiosError: true,
      response: {
        status: 400,
        data: {
          message: "Could not extract readable text from the uploaded resume. Please upload a text-based PDF.",
          detail: "Could not extract readable text from the uploaded resume. Please upload a text-based PDF.",
          requestId: "req-123"
        }
      }
    };

    const mapped = getAnalysisErrorInfo(error);

    expect(mapped.friendly).toContain("text-based PDF");
    expect(mapped.requestId).toBe("req-123");
  });
});
