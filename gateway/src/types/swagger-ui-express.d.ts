declare module "swagger-ui-express" {
  import { RequestHandler } from "express";

  export const serve: RequestHandler[];
  export function setup(
    swaggerDoc?: any,
    opts?: any,
    options?: any,
    customCss?: any,
    customfavIcon?: any,
    swaggerUrl?: any,
    customeSiteTitle?: any
  ): RequestHandler;
  export function serveFiles(swaggerDoc?: any, opts?: any): RequestHandler[];
  export function generateHTML(swaggerDoc?: any, opts?: any, options?: any, customCss?: any, customfavIcon?: any, swaggerUrl?: any, customeSiteTitle?: any): string;
}
