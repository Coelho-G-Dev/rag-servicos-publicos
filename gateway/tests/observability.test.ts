import request from "supertest";
import { createApp } from "../src/app";

describe("Observabilidade (Health, Ready e Metrics)", () => {
  const app = createApp();

  it("GET /health deve retornar status 200 e informações do serviço", async () => {
    const res = await request(app).get("/health");

    expect(res.status).toBe(200);
    expect(res.body.status).toBe("healthy");
    expect(res.body.service).toBe("rag-gateway");
    expect(res.body.uptime).toBeDefined();
  });

  it("GET /metrics deve expor métricas no formato Prometheus", async () => {
    const res = await request(app).get("/metrics");

    expect(res.status).toBe(200);
    expect(res.text).toContain("http_requests_total");
    expect(res.text).toContain("chat_requests_total");
  });

  it("GET /ready deve responder adequadamente com status dos checks", async () => {
    const res = await request(app).get("/ready");

    expect([200, 503]).toContain(res.status);
    expect(res.body.checks).toBeDefined();
  });

  it("GET /api-docs.json deve retornar a especificação OpenAPI 3.0", async () => {
    const res = await request(app).get("/api-docs.json");

    expect(res.status).toBe(200);
    expect(res.body.openapi).toBe("3.0.3");
    expect(res.body.info.title).toContain("RAG Serviços Públicos");
    expect(res.body.paths["/api/v1/chat"]).toBeDefined();
  });

  it("GET /docs deve redirecionar ou servir o Swagger UI", async () => {
    const res = await request(app).get("/docs/");

    expect([200, 301, 302]).toContain(res.status);
  });
});
