import { Request, Response, NextFunction } from "express";
import { v4 as uuidv4 } from "uuid";

declare global {
  namespace Express {
    interface Request {
      id?: string;
    }
  }
}

export const requestIdMiddleware = (req: Request, res: Response, next: NextFunction) => {
  const incomingId = req.header("x-request-id");
  const requestId = incomingId && incomingId.trim() !== "" ? incomingId : uuidv4();

  req.id = requestId;
  res.setHeader("X-Request-Id", requestId);

  next();
};
