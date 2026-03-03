import { isAxiosError } from "axios";

export type ErrorState = {
  friendly: string;
  technical?: string;
  requestId?: string;
};

function stringifyDetail(detail: unknown): string | undefined {
  if (!detail) return undefined;
  if (typeof detail === "string") return detail;
  try {
    return JSON.stringify(detail, null, 2);
  } catch {
    return String(detail);
  }
}

export function getAnalysisErrorInfo(error: unknown): ErrorState {
  if (!isAxiosError(error)) {
    return { friendly: "Analysis failed. Please try again." };
  }

  if (error.code === "ERR_NETWORK") {
    return {
      friendly: "Backend service is unreachable. Please start backend on port 8080 and ML on 8000.",
      technical: error.message
    };
  }

  const status = error.response?.status;
  const payload = error.response?.data as { message?: unknown; detail?: unknown; requestId?: unknown } | undefined;
  const message = typeof payload?.message === "string" ? payload.message : "";
  const detailRaw = payload?.detail;
  const detailText = stringifyDetail(detailRaw);
  const requestId = typeof payload?.requestId === "string" ? payload.requestId : undefined;
  const combined = `${message} ${detailText ?? ""}`.toLowerCase();

  if (combined.includes("could not extract readable text") || combined.includes("text-based pdf")) {
    return {
      friendly: "We couldn't read text from this PDF. Please upload a text-based PDF (not a scanned image), then try again.",
      technical: detailText,
      requestId
    };
  }

  if (status === 422) {
    return {
      friendly: "Could not process resume data. Please verify the file content and try again.",
      technical: detailText ?? message,
      requestId
    };
  }

  if (status === 429) {
    return {
      friendly: "Too many analysis requests. Please wait a minute and try again.",
      technical: detailText ?? message,
      requestId
    };
  }

  return {
    friendly: detailText || message || "Analysis failed. Please try again.",
    technical: detailText && detailText !== message ? detailText : undefined,
    requestId
  };
}
