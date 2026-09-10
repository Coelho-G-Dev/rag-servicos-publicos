import { Request, Response } from "express";
import { Pool } from "pg";
import { config } from "../config";
import { logger } from "./logger";

export const createHealthController = (pgPool?: Pool) => {
  const getHealth = (req: Request, res: Response) => {
    res.status(200).json({
      status: "healthy",
      service: "rag-gateway",
      uptime: process.uptime(),
      timestamp: new Date().toISOString(),
    });
  };

  const getReady = async (req: Request, res: Response) => {
    let dbStatus = "unknown";
    let aiServiceStatus = "unknown";
    let isReady = true;

    if (pgPool) {
      try {
        await pgPool.query("SELECT 1;");
        dbStatus = "connected";
      } catch (err: any) {
        dbStatus = `disconnected: ${err.message}`;
        isReady = false;
      }
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    try {
      const resp = await fetch(`${config.AI_SERVICE_URL}/health`, {
        signal: controller.signal,
      });
      aiServiceStatus = resp.ok ? "connected" : `degraded (${resp.status})`;
      if (!resp.ok) isReady = false;
    } catch (err: any) {
      aiServiceStatus = `unreachable: ${err.message}`;
      isReady = false;
    } finally {
      clearTimeout(timeoutId);
    }

    const statusCode = isReady ? 200 : 503;
    res.status(statusCode).json({
      status: isReady ? "ready" : "not_ready",
      checks: {
        database: dbStatus,
        aiService: aiServiceStatus,
      },
    });
  };

  return { getHealth, getReady };
};
