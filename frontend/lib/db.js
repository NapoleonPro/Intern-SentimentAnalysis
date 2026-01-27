import { Pool } from 'pg';
const pool = new Pool({
  user: 'postgres',
  password: 'admin', 
  host: 'localhost',
  port: 5432,
  database: 'db_pkp_aceh',
});
export const query = (text, params) => pool.query(text, params);