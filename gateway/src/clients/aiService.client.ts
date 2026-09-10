import { config } from "../config";
import { logger } from "../observability/logger";

export interface AIServiceSource {
  id: string;
  nome: string;
  categoria: string;
  endereco: string;
  similarity?: number;
}

export interface AIServiceResponse {
  answer: string;
  sources: AIServiceSource[];
  retrieved_chunks: any[];
}

export class AIServiceClient {
  private baseUrl: string;
  private secret: string;

  constructor(baseUrl?: string, secret?: string) {
    let rawUrl = (baseUrl || config.AI_SERVICE_URL).trim();
    if (rawUrl && !rawUrl.startsWith("http://") && !rawUrl.startsWith("https://")) {
      if (rawUrl.includes("localhost") || rawUrl.includes("127.0.0.1") || rawUrl.includes(":") || !rawUrl.includes(".")) {
        rawUrl = `http://${rawUrl}`;
      } else {
        rawUrl = `https://${rawUrl}`;
      }
    }
    this.baseUrl = rawUrl.replace(/\/+$/, "");
    this.secret = secret || config.INTERNAL_API_SECRET;
  }

  async query(message: string, requestId?: string): Promise<AIServiceResponse> {
    const url = `${this.baseUrl}/internal/rag/query`;
    logger.info({ request_id: requestId, url }, "calling_ai_service");

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 60000);

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Internal-Secret": this.secret,
          ...(requestId ? { "X-Request-Id": requestId } : {}),
        },
        body: JSON.stringify({ message }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorBody = await response.text();
        logger.error(
          { status: response.status, body: errorBody, request_id: requestId },
          "ai_service_call_failed"
        );
        throw new Error(`AI Service respondeu com status ${response.status}: ${errorBody}`);
      }

      const data = (await response.json()) as AIServiceResponse;
      return data;
    } catch (error: any) {
      if (error.name === "AbortError") {
        throw new Error("Timeout ao aguardar resposta do AI Service.");
      }
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }
}

export const aiServiceClient = new AIServiceClient();
