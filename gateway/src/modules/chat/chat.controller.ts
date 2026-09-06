import { Request, Response, NextFunction } from "express";
import { chatService, ChatService } from "./chat.service";
import { chatRequestsTotal } from "../../observability/metrics";

export class ChatController {
  constructor(private service: ChatService = chatService) {}

  handleChat = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { message } = req.body;

      if (!message || typeof message !== "string" || message.trim() === "") {
        return res.status(400).json({
          status: 400,
          error: "ValidationError",
          message: "O campo 'message' é obrigatório e deve conter uma string não vazia.",
        });
      }

      const result = await this.service.ask(message.trim(), req.id);
      chatRequestsTotal.inc({ status: "success" });

      return res.status(200).json({
        answer: result.answer,
        sources: result.sources,
      });
    } catch (error: any) {
      chatRequestsTotal.inc({ status: "error" });
      next(error);
    }
  };
}

export const chatController = new ChatController();
