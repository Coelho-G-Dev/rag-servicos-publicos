import request from "supertest";
import { createApp } from "../src/app";
import { ServicesController } from "../src/modules/services/services.controller";
import { ServicesService } from "../src/modules/services/services.service";
import { ServicesRepository } from "../src/modules/services/services.repository";

describe("GET /api/v1/services", () => {
  let mockRepo: jest.Mocked<ServicesRepository>;
  let app: any;

  beforeEach(() => {
    mockRepo = {
      findServices: jest.fn(),
    } as any;

    const service = new ServicesService(mockRepo);
    const controller = new ServicesController(service);

    app = createApp({ servicesController: controller });
  });

  it("deve retornar lista de serviços e total com sucesso", async () => {
    const mockServices = [
      {
        id: "cul-001",
        nome: "Teatro Arthur Azevedo",
        categoria: "Cultura",
        descricao: "Segundo teatro mais antigo do Brasil.",
        endereco: "Rua do Sol, 180 - Centro",
        created_at: new Date().toISOString(),
      },
    ];

    mockRepo.findServices.mockResolvedValueOnce(mockServices);

    const response = await request(app).get("/api/v1/services?category=Cultura");

    expect(response.status).toBe(200);
    expect(response.body.total).toBe(1);
    expect(response.body.services).toHaveLength(1);
    expect(response.body.services[0].nome).toBe("Teatro Arthur Azevedo");
    expect(mockRepo.findServices).toHaveBeenCalledWith(
      expect.objectContaining({ category: "Cultura" })
    );
  });

  it("deve repassar parâmetros de busca 'q' ao repositório", async () => {
    mockRepo.findServices.mockResolvedValueOnce([]);

    const response = await request(app).get("/api/v1/services?q=vacina");

    expect(response.status).toBe(200);
    expect(mockRepo.findServices).toHaveBeenCalledWith(
      expect.objectContaining({ q: "vacina" })
    );
  });
});
