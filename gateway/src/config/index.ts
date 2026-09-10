import dotenv from "dotenv";

dotenv.config();

function normalizeServiceUrl(url?: string): string {
  if (!url) return "http://localhost:8000";
  const trimmed = url.trim();
  if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
    return trimmed.replace(/\/+$/, "");
  }
  // Se for hostname local ou interno com porta (ex: localhost:8000, 127.0.0.1:8000, service:8000)
  if (trimmed.includes("localhost") || trimmed.includes("127.0.0.1") || trimmed.includes(":")) {
    return `http://${trimmed}`.replace(/\/+$/, "");
  }
  // Se for domínio com ponto (ex: meu-servico.onrender.com)
  if (trimmed.includes(".")) {
    return `https://${trimmed}`.replace(/\/+$/, "");
  }
  // Se for um identificador curto de serviço no Render (ex: rag-ai-service-jsd6)
  return `https://${trimmed}.onrender.com`;
}

export const config = {
  PORT: parseInt((process.env.PORT || "3000").trim(), 10),
  NODE_ENV: (process.env.NODE_ENV || "development").trim(),
  AI_SERVICE_URL: normalizeServiceUrl(process.env.AI_SERVICE_URL),
  INTERNAL_API_SECRET: (process.env.INTERNAL_API_SECRET || "super-secret-internal-key").trim(),
  
  DATABASE_URL: (process.env.DATABASE_URL || "postgresql://rag_user:rag_password@localhost:5432/rag_db").trim(),
  
  RATE_LIMIT_WINDOW_MS: parseInt((process.env.RATE_LIMIT_WINDOW_MS || "60000").trim(), 10),
  RATE_LIMIT_MAX: parseInt((process.env.RATE_LIMIT_MAX || "100").trim(), 10),
};

