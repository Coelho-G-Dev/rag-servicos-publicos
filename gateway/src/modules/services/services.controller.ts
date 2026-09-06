import { Request, Response, NextFunction } from "express";
import { ServicesService } from "./services.service";

export class ServicesController {
  constructor(private service: ServicesService) {}

  listServices = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const category = req.query.category as string | undefined;
      const q = req.query.q as string | undefined;
      const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : undefined;
      const offset = req.query.offset ? parseInt(req.query.offset as string, 10) : undefined;

      const services = await this.service.searchServices({
        category,
        q,
        limit,
        offset,
      });

      return res.status(200).json({
        total: services.length,
        services,
      });
    } catch (error) {
      next(error);
    }
  };
}
