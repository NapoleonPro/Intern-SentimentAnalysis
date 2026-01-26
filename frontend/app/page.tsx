import { query } from '../lib/db';
import DashboardClient from './DashboardClient';

// force dynamic rendering
export const dynamic = 'force-dynamic';

async function getArticles() {
  try {
    const res = await query(
      "SELECT * FROM articles WHERE sentiment_label IS NOT NULL ORDER BY published_date DESC"
    );
    return res.rows.map((row: any) => ({
      ...row,
      // published_date is now passed as-is from the database
      // extract domain name
      media_name: new URL(row.url).hostname.replace('www.', '')
    }));
  } catch (error) {
    console.error(error);
    return [];
  }
}

export default async function Dashboard() {
  const data = await getArticles();

  return <DashboardClient initialData={data} />;
}