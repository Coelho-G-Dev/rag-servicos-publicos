import { Request, Response, NextFunction } from "express";
import { logger } from "../observability/logger";
import { httpRequestDurationSeconds, httpRequestsTotal } from "../observability/metrics";

export const requestLoggerMiddleware = (req: Request, res: Response, next: NextFunction) => {
  const start = process.hrtime();

  res.on("finish", () => {
    const diff = process.hrtime(start);
    const durationMs = (diff[0] * 1e3 + diff[1] * 1e-6);
    const durationSec = durationMs / 1000;
    const status = res.statusCode;
    const method = req.method;
    const path = req.route ? req.baseUrl + req.route.path : req.path;

    logger.info({
      method,
      path: req.originalUrl || req.url,
      status,
      duration_ms: Math.round(durationMs * 100) / 100,
      request_id: req.id || "unknown",
    }, "http_request_completed");

    httpRequestsTotal.inc({ method, path, status: status.toString() });
    httpRequestDurationSeconds.observe({ method, path, status: status.toString() }, durationSec);
  });

  next();
};
