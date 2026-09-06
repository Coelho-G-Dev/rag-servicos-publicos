import client from "prom-client";

client.collectDefaultMetrics({ prefix: "gateway_" });

export const httpRequestsTotal = new client.Counter({
  name: "http_requests_total",
  help: "Total de requisições HTTP recebidas pelo Gateway",
  labelNames: ["method", "path", "status"],
});

export const httpRequestDurationSeconds = new client.Histogram({
  name: "http_request_duration_seconds",
  help: "Duração das requisições HTTP em segundos",
  labelNames: ["method", "path", "status"],
  buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
});

export const chatRequestsTotal = new client.Counter({
  name: "chat_requests_total",
  help: "Total de requisições de conversação RAG processadas no Gateway",
  labelNames: ["status"],
});

export const getMetrics = async (): Promise<string> => {
  return await client.register.metrics();
};

export const getMetricsContentType = (): string => {
  return client.register.contentType;
};
