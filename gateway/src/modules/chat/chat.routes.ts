import { Router } from "express";
import { chatController, ChatController } from "./chat.controller";

export const createChatRouter = (controller: ChatController = chatController): Router => {
  const router = Router();
  router.post("/", controller.handleChat);
  return router;
};

export const chatRouter = createChatRouter();
