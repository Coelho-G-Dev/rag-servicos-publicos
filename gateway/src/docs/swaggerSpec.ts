export const swaggerSpec = {
  openapi: "3.0.3",
  info: {
    title: "RAG Serviços Públicos - São Luís/MA (Gateway API)",
    version: "1.0.0",
    description: `
API Gateway pública para o sistema de RAG (Retrieval-Augmented Generation) sobre serviços públicos de São Luís/MA.

### Recursos:
- **Chat com IA**: Respostas fundamentadas estritamente em serviços públicos reais da cidade (sem alucinações).
- **Busca Direta**: Listagem e filtragem de serviços diretamente no banco relacional sem IA.
- **Observabilidade**: Métricas Prometheus e endpoints de verificação de integridade (Health e Ready).
    `,
    contact: {
      name: "Suporte RAG São Luís",
      url: "https://github.com/",
    },
  },
  servers: [
    {
      url: "/",
      description: "Servidor Atual",
    },
  ],
  paths: {
    "/api/v1/chat": {
      post: {
        summary: "Consulta RAG com IA sobre serviços públicos de São Luís",
        description:
          "Recebe uma pergunta em linguagem natural, busca os serviços mais relevantes via pgvector e gera uma resposta fundamentada com o Google Gemini.",
        tags: ["Chat RAG"],
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["message"],
                properties: {
                  message: {
                    type: "string",
                    example: "Onde posso encontrar atendimento médico de urgência 24 horas em São Luís?",
                    description: "Dúvida ou solicitação do cidadão",
                  },
                },
              },
            },
          },
        },
        responses: {
          "200": {
            description: "Resposta gerada e fundamentada com lista de fontes oficiais",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    answer: {
                      type: "string",
                      example:
                        "Para atendimento médico de urgência 24 horas em São Luís, você pode se dirigir à UPA Vinhais, localizada na Av. Jerônimo de Albuquerque, s/n - Vinhais, ou ao Hospital Municipal Djalma Marques (Socorrão I) na Rua do Passeio, s/n - Centro.",
                    },
                    sources: {
                      type: "array",
                      items: {
                        type: "object",
                        properties: {
                          id: { type: "string", example: "sau-002" },
                          nome: { type: "string", example: "UPA Vinhais" },
                          categoria: { type: "string", example: "Saúde" },
                          endereco: {
                            type: "string",
                            example: "Av. Jerônimo de Albuquerque, s/n - Vinhais, São Luís - MA",
                          },
                          similarity: { type: "number", example: 0.8841 },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          "400": {
            description: "Requisição inválida (mensagem ausente ou vazia)",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    status: { type: "integer", example: 400 },
                    error: { type: "string", example: "ValidationError" },
                    message: {
                      type: "string",
                      example: "O campo 'message' é obrigatório e deve conter uma string não vazia.",
                    },
                  },
                },
              },
            },
          },
          "500": {
            description: "Erro interno no servidor ou indisponibilidade do AI Service",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    status: { type: "integer", example: 500 },
                    error: { type: "string", example: "InternalServerError" },
                    message: { type: "string", example: "Erro ao processar resposta do AI Service" },
                    request_id: { type: "string", example: "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d" },
                  },
                },
              },
            },
          },
        },
      },
    },
    "/api/v1/services": {
      get: {
        summary: "Busca direta de serviços públicos cadastrados (sem IA)",
        description:
          "Permite buscar e filtrar serviços públicos por categoria e palavra-chave no banco de dados relacional.",
        tags: ["Serviços Públicos"],
        parameters: [
          {
            name: "category",
            in: "query",
            required: false,
            schema: {
              type: "string",
              enum: ["Saúde", "Educação", "Assistência Social", "Cultura", "Cidadania"],
            },
            description: "Filtrar por categoria específica",
            example: "Saúde",
          },
          {
            name: "q",
            in: "query",
            required: false,
            schema: { type: "string" },
            description: "Termo de busca textual no nome, descrição ou endereço",
            example: "vinhais",
          },
          {
            name: "limit",
            in: "query",
            required: false,
            schema: { type: "integer", default: 50, maximum: 100 },
            description: "Quantidade máxima de registros retornados",
          },
          {
            name: "offset",
            in: "query",
            required: false,
            schema: { type: "integer", default: 0 },
            description: "Deslocamento de paginação",
          },
        ],
        responses: {
          "200": {
            description: "Lista de serviços públicos encontrados",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    total: { type: "integer", example: 1 },
                    services: {
                      type: "array",
                      items: {
                        type: "object",
                        properties: {
                          id: { type: "string", example: "sau-002" },
                          nome: { type: "string", example: "UPA Vinhais" },
                          categoria: { type: "string", example: "Saúde" },
                          descricao: {
                            type: "string",
                            example:
                              "Unidade de Pronto Atendimento 24h para emergências clínicas e pediátricas...",
                          },
                          endereco: {
                            type: "string",
                            example: "Av. Jerônimo de Albuquerque, s/n - Vinhais, São Luís - MA",
                          },
                          created_at: { type: "string", example: "2026-09-04T00:00:00.000Z" },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
    },
    "/health": {
      get: {
        summary: "Liveness Check",
        description: "Verifica se o processo do Gateway está em execução.",
        tags: ["Observabilidade"],
        responses: {
          "200": {
            description: "Gateway saudável",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    status: { type: "string", example: "healthy" },
                    service: { type: "string", example: "rag-gateway" },
                    uptime: { type: "number", example: 142.5 },
                    timestamp: { type: "string", example: "2026-09-04T01:30:00.000Z" },
                  },
                },
              },
            },
          },
        },
      },
    },
    "/ready": {
      get: {
        summary: "Readiness Check",
        description: "Verifica se os componentes dependentes (PostgreSQL e AI Service) estão acessíveis.",
        tags: ["Observabilidade"],
        responses: {
          "200": {
            description: "Todos os serviços conectados e prontos para tráfego",
          },
          "503": {
            description: "Um ou mais serviços dependentes indisponíveis",
          },
        },
      },
    },
    "/metrics": {
      get: {
        summary: "Métricas Prometheus",
        description:
          "Expõe métricas no padrão Prometheus (http_requests_total, chat_requests_total, latência, CPU e memória).",
        tags: ["Observabilidade"],
        responses: {
          "200": {
            description: "Métricas formatadas em texto puro",
            content: {
              "text/plain": {
                schema: { type: "string" },
              },
            },
          },
        },
      },
    },
  },
};
