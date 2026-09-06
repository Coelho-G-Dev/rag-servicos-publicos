import { Router } from "express";
import { ServicesController } from "./services.controller";

export const createServicesRouter = (controller: ServicesController): Router => {
  const router = Router();
  router.get("/", controller.listServices);
  return router;
};
