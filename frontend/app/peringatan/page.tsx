import Link from 'next/link';
import { query } from '../../lib/db';

// force dynamic rendering
export const dynamic = 'force-dynamic';

interface Article {
  id: number;
  title: string;
  content: string;
  url: string;
  published_date: string;
  created_at: string;
  media_name: string;
}

async function getNegativeArticles(): Promise<Article[]> {
  try {
    const res = await query(
      "SELECT * FROM articles WHERE sentiment_label = 'Negatif' ORDER BY created_at DESC"
    );
    return res.rows.map((row: any) => ({
      ...row,
      media_name: new URL(row.url).hostname.replace('www.', ''),
      published_date: new Date(row.published_date).toLocaleDateString('id-ID', {
        day: 'numeric', month: 'short', year: 'numeric'
      }),
    }));
  } catch (error) {
    console.error("Failed to fetch negative articles:", error);
    return [];
  }
}

// Reusable ArticleItem component
function ArticleItem({ item }: { item: Article }) {
  return (
    <div className="bg-white p-5 rounded-xl shadow-sm shadow-slate-200/50 hover:shadow-md transition-all duration-300">
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-slate-800 text-base leading-snug mb-2">
            {item.title}
          </h3>
          <div className="flex items-center gap-3 text-xs text-slate-500 mb-2">
            <span className="flex items-center gap-1">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3.5 h-3.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {item.published_date}
            </span>
            <span className="bg-slate-100 text-slate-700 px-2 py-1 rounded font-medium text-xs">
              {item.media_name}
            </span>
          </div>
          <p className="text-sm text-slate-500 leading-relaxed line-clamp-2">{item.content}</p>
        </div>
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-xs font-semibold shadow-sm transition-colors flex items-center gap-2"
        >
          Buka
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3.5 h-3.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
          </svg>
        </a>
      </div>
    </div>
  );
}


export default async function PeringatanPage() {
  const negativeArticles = await getNegativeArticles();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-50 to-red-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200/60 sticky top-0 z-50">
        <div className="w-full px-8 py-5">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
               <div className="w-12 h-12 bg-gradient-to-br from-red-600 to-rose-600 rounded-xl flex items-center justify-center shadow-lg shadow-red-500/20">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-white">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                  Semua Isu Negatif
                </h1>
                <p className="text-sm text-slate-500">Total terdeteksi: {negativeArticles.length} isu</p>
              </div>
            </div>
            <Link href="/" className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2">
              &larr; Kembali ke Dashboard
            </Link>
          </div>
        </div>
      </header>

      <main className="w-full px-8 py-8">
        <div className="grid grid-cols-1 gap-4">
          {negativeArticles.length > 0 ? (
            negativeArticles.map(item => <ArticleItem key={item.id} item={item} />)
          ) : (
            <div className="text-center py-20">
              <p className="text-lg font-semibold text-slate-600">Tidak ada isu negatif yang terdeteksi.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
