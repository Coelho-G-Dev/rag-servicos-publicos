import request from "supertest";
import { createApp } from "../src/app";
import { ChatController } from "../src/modules/chat/chat.controller";
import { ChatService } from "../src/modules/chat/chat.service";
import { createChatRouter } from "../src/modules/chat/chat.routes";
import { AIServiceClient } from "../src/clients/aiService.client";

describe("POST /api/v1/chat", () => {
  let mockClient: jest.Mocked<AIServiceClient>;
  let app: any;

  beforeEach(() => {
    mockClient = {
      query: jest.fn(),
    } as any;

    const chatService = new ChatService(mockClient);
    const chatController = new ChatController(chatService);
    const chatRouterOverride = createChatRouter(chatController);

    app = createApp({ chatRouterOverride });
  });

  it("deve retornar 200 com resposta e fontes quando a mensagem for válida", async () => {
    mockClient.query.mockResolvedValueOnce({
      answer: "A UPA Vinhais funciona 24 horas por dia.",
      sources: [
        {
          id: "sau-002",
          nome: "UPA Vinhais",
          categoria: "Saúde",
          endereco: "Av. Jerônimo de Albuquerque, s/n - Vinhais",
          similarity: 0.92,
        },
      ],
      retrieved_chunks: [],
    });

    const response = await request(app)
      .post("/api/v1/chat")
      .send({ message: "Qual o horário da UPA Vinhais?" });

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      answer: "A UPA Vinhais funciona 24 horas por dia.",
      sources: [
        {
          id: "sau-002",
          nome: "UPA Vinhais",
          categoria: "Saúde",
          endereco: "Av. Jerônimo de Albuquerque, s/n - Vinhais",
          similarity: 0.92,
        },
      ],
    });
    expect(response.headers["x-request-id"]).toBeDefined();
  });

  it("deve retornar 400 se o campo 'message' estiver ausente ou vazio", async () => {
    const response = await request(app).post("/api/v1/chat").send({ message: "" });

    expect(response.status).toBe(400);
    expect(response.body.error).toBe("ValidationError");
  });

  it("deve propagar erro 500 se o AI Service falhar", async () => {
    mockClient.query.mockRejectedValueOnce(new Error("AI Service indisponível"));

    const response = await request(app)
      .post("/api/v1/chat")
      .send({ message: "Onde tem vacina?" });

    expect(response.status).toBe(500);
    expect(response.body.message).toContain("AI Service indisponível");
  });
});
