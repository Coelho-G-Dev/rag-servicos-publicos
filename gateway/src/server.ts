import { createApp } from "./app";
import { config } from "./config";
import { logger } from "./observability/logger";

const app = createApp();

const server = app.listen(config.PORT, () => {
  logger.info(
    { port: config.PORT, env: config.NODE_ENV, ai_service_url: config.AI_SERVICE_URL },
    `RAG Gateway iniciado com sucesso na porta ${config.PORT}`
  );
});

const gracefulShutdown = (signal: string) => {
  logger.info({ signal }, "Recebido sinal de desligamento, encerrando servidor...");
  server.close(() => {
    logger.info("Servidor HTTP encerrado com sucesso.");
    process.exit(0);
  });
};

process.on("SIGTERM", () => gracefulShutdown("SIGTERM"));
process.on("SIGINT", () => gracefulShutdown("SIGINT"));
