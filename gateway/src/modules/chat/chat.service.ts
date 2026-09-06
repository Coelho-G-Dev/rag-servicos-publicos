import { AIServiceClient, aiServiceClient, AIServiceSource } from "../../clients/aiService.client";

export interface ChatResult {
  answer: string;
  sources: AIServiceSource[];
}

export class ChatService {
  constructor(private client: AIServiceClient = aiServiceClient) {}

  async ask(message: string, requestId?: string): Promise<ChatResult> {
    const response = await this.client.query(message, requestId);
    return {
      answer: response.answer,
      sources: response.sources,
    };
  }
}

export const chatService = new ChatService();
