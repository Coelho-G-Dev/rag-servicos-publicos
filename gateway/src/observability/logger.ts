import pino from "pino";
import { config } from "../config";

export const logger = pino({
  level: config.NODE_ENV === "test" ? "silent" : "info",
  formatters: {
    level: (label) => ({ level: label }),
  },
  timestamp: pino.stdTimeFunctions.isoTime,
});
