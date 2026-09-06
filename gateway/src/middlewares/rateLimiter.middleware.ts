import rateLimit from "express-rate-limit";
import { config } from "../config";

export const rateLimiterMiddleware = rateLimit({
  windowMs: config.RATE_LIMIT_WINDOW_MS,
  max: config.RATE_LIMIT_MAX,
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    status: 429,
    error: "Too Many Requests",
    message: "Limite de requisições excedido. Por favor, tente novamente em alguns instantes.",
  },
});
