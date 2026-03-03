import { NextFunction, Request, Response } from "express";
import axios from "axios";

export function errorMiddleware(error: Error, req: Request, res: Response, _next: NextFunction) {
  const requestId = req.requestId;
  const elapsedMs = Date.now() - (req.requestStartTime ?? Date.now());

  if (axios.isAxiosError(error)) {
    const status = error.response?.status ?? 502;
    const detailPayload = error.response?.data;
    const detail =
      typeof detailPayload === "string"
        ? detailPayload
        : detailPayload && typeof detailPayload === "object" && "detail" in detailPayload
          ? (detailPayload as { detail?: unknown }).detail
          : detailPayload && typeof detailPayload === "object" && "message" in detailPayload
            ? (detailPayload as { message?: unknown }).message
            : error.message;

    console.error(
      `[trace] requestId=${requestId ?? "n/a"} method=${req.method} path=${req.originalUrl} status=${status} elapsedMs=${elapsedMs} upstream=ml error=${error.message}`
    );

    return res.status(status).json({
      message: "Upstream service error",
      detail,
      requestId,
      upstreamStatus: status,
      elapsedMs
    });
  }

  console.error(
    `[trace] requestId=${requestId ?? "n/a"} method=${req.method} path=${req.originalUrl} status=500 elapsedMs=${elapsedMs} error=${error.message}`
  );

  return res.status(500).json({
    message: "Internal server error",
    detail: error.message,
    requestId,
    elapsedMs
  });
}
