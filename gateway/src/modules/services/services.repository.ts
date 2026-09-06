import { Pool } from "pg";

export interface PublicServiceRecord {
  id: string;
  nome: string;
  categoria: string;
  descricao: string;
  endereco: string;
  created_at: string;
}

export interface ServicesFilter {
  category?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export class ServicesRepository {
  constructor(private pool: Pool) {}

  async findServices(filters: ServicesFilter): Promise<PublicServiceRecord[]> {
    const conditions: string[] = [];
    const values: any[] = [];
    let paramIndex = 1;

    if (filters.category && filters.category.trim() !== "") {
      conditions.push(`LOWER(categoria) = LOWER($${paramIndex++})`);
      values.push(filters.category.trim());
    }

    if (filters.q && filters.q.trim() !== "") {
      conditions.push(`(nome ILIKE $${paramIndex} OR descricao ILIKE $${paramIndex} OR endereco ILIKE $${paramIndex})`);
      values.push(`%${filters.q.trim()}%`);
      paramIndex++;
    }

    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";
    const limit = Math.min(filters.limit || 50, 100);
    const offset = filters.offset || 0;

    const query = `
      SELECT id, nome, categoria, descricao, endereco, created_at
      FROM public_services
      ${whereClause}
      ORDER BY nome ASC
      LIMIT $${paramIndex++} OFFSET $${paramIndex++}
    `;

    values.push(limit, offset);

    const { rows } = await this.pool.query(query, values);
    return rows;
  }
}
