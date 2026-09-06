import dotenv from "dotenv";

dotenv.config();

export const config = {
  PORT: parseInt(process.env.PORT || "3000", 10),
  NODE_ENV: process.env.NODE_ENV || "development",
  AI_SERVICE_URL: process.env.AI_SERVICE_URL || "http://localhost:8000",
  INTERNAL_API_SECRET: process.env.INTERNAL_API_SECRET || "super-secret-internal-key",
  
  DATABASE_URL: process.env.DATABASE_URL || "postgresql://rag_user:rag_password@localhost:5432/rag_db",
  
  RATE_LIMIT_WINDOW_MS: parseInt(process.env.RATE_LIMIT_WINDOW_MS || "60000", 10),
  RATE_LIMIT_MAX: parseInt(process.env.RATE_LIMIT_MAX || "100", 10),
};
