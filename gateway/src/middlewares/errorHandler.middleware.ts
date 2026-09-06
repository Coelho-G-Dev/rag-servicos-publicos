import { Request, Response, NextFunction } from "express";
import { logger } from "../observability/logger";

export const errorHandlerMiddleware = (
  err: any,
  req: Request,
  res: Response,
  next: NextFunction
) => {
  const status = err.status || err.statusCode || 500;
  const message = err.message || "Erro interno no servidor";
  const requestId = req.id || "unknown";

  logger.error({
    request_id: requestId,
    method: req.method,
    path: req.originalUrl || req.url,
    status,
    error: message,
    stack: err.stack,
  }, "unhandled_request_error");

  res.status(status).json({
    status,
    error: err.name || "InternalServerError",
    message,
    request_id: requestId,
  });
};
