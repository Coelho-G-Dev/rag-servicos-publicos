import { ServicesRepository, PublicServiceRecord, ServicesFilter } from "./services.repository";

export class ServicesService {
  constructor(private repo: ServicesRepository) {}

  async searchServices(filter: ServicesFilter): Promise<PublicServiceRecord[]> {
    return await this.repo.findServices(filter);
  }
}
