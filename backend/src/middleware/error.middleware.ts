import { NextFunction, Request, Response } from "express";

export function errorMiddleware(error: Error, _req: Request, res: Response, _next: NextFunction) {
  return res.status(500).json({ message: "Internal server error", detail: error.message });
}
