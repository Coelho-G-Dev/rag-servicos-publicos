import express, { Express, Request, Response } from "express";
import cors from "cors";
import helmet from "helmet";
import { Pool } from "pg";
import { config } from "./config";
import { requestIdMiddleware } from "./middlewares/requestId.middleware";
import { requestLoggerMiddleware } from "./middlewares/requestLogger.middleware";
import { rateLimiterMiddleware } from "./middlewares/rateLimiter.middleware";
import { errorHandlerMiddleware } from "./middlewares/errorHandler.middleware";
import { createHealthController } from "./observability/health";
import { getMetrics, getMetricsContentType } from "./observability/metrics";
import { createChatRouter, chatRouter } from "./modules/chat/chat.routes";
import { createServicesRouter } from "./modules/services/services.routes";
import { ServicesController } from "./modules/services/services.controller";
import { ServicesService } from "./modules/services/services.service";
import { ServicesRepository } from "./modules/services/services.repository";

import swaggerUi from "swagger-ui-express";
import { swaggerSpec } from "./docs/swaggerSpec";

export interface AppDependencies {
  pgPool?: Pool;
  servicesController?: ServicesController;
  chatRouterOverride?: express.Router;
}

export const createApp = (deps?: AppDependencies): Express => {
  const app = express();

  app.use(
    helmet({
      contentSecurityPolicy: false,
    })
  );
  app.use(cors());
  app.use(express.json());

  app.use(requestIdMiddleware);
  app.use(requestLoggerMiddleware);

  app.use("/docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));
  app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));
  app.get("/api-docs.json", (req: Request, res: Response) => {
    res.setHeader("Content-Type", "application/json");
    res.send(swaggerSpec);
  });

  const healthController = createHealthController(deps?.pgPool);
  app.get("/health", healthController.getHealth);
  app.get("/ready", healthController.getReady);

  app.get("/metrics", async (req: Request, res: Response) => {
    res.setHeader("Content-Type", getMetricsContentType());
    res.send(await getMetrics());
  });

  app.use("/api/", rateLimiterMiddleware);

  if (deps?.chatRouterOverride) {
    app.use("/api/v1/chat", deps.chatRouterOverride);
  } else {
    app.use("/api/v1/chat", chatRouter);
  }

  let servicesController = deps?.servicesController;
  if (!servicesController) {
    const pool = deps?.pgPool || new Pool({ connectionString: config.DATABASE_URL });
    const repo = new ServicesRepository(pool);
    const service = new ServicesService(repo);
    servicesController = new ServicesController(service);
  }
  app.use("/api/v1/services", createServicesRouter(servicesController));

  app.use((req: Request, res: Response) => {
    res.status(404).json({
      status: 404,
      error: "NotFound",
      message: `Rota ${req.method} ${req.originalUrl} não encontrada.`,
    });
  });

  app.use(errorHandlerMiddleware);

  return app;
};
