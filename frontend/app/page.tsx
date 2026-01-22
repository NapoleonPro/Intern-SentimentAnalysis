import { query } from '../lib/db';

// force dynamic rendering
export const dynamic = 'force-dynamic';

async function getArticles() {
  try {
    const res = await query(
      "SELECT * FROM articles WHERE sentiment_label IS NOT NULL ORDER BY published_date DESC"
    );
    return res.rows.map((row: any) => ({
      ...row,
      published_date: new Date(row.published_date).toLocaleDateString('id-ID', {
        day: 'numeric', month: 'short', year: 'numeric'
      }),
      // extract domain name
      media_name: new URL(row.url).hostname.replace('www.', ''),
      created_at: null 
    }));
  } catch (error) {
    console.error(error);
    return [];
  }
}

export default async function Dashboard() {
  const data = await getArticles();

  // filter data
  const total = data.length;
  const negList = data.filter((x: any) => x.sentiment_label === 'Negatif');
  const posList = data.filter((x: any) => x.sentiment_label === 'Positif');
  const neuList = data.filter((x: any) => x.sentiment_label === 'Netral');

  return (
    <main className="min-h-screen bg-slate-50 p-8 font-sans">
      
      {/* HEADER */}
      <div className="flex justify-between items-end mb-8 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">Dashboard EWS</h1>
          <p className="text-slate-500 text-sm mt-1">Sistem Peringatan Dini Opini Publik - Pemerintah Aceh</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-400 uppercase font-semibold">Update Terakhir</p>
          <p className="text-sm font-medium text-slate-700">{new Date().toLocaleString('id-ID')}</p>
        </div>
      </div>

      {/* METRICS CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-5 rounded-lg shadow-sm border border-slate-200">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Berita</p>
          <p className="text-3xl font-bold text-slate-800 mt-1">{total}</p>
        </div>
        <div className="bg-white p-5 rounded-lg shadow-sm border border-green-200 bg-green-50/30">
          <p className="text-xs font-bold text-green-600 uppercase tracking-wider">Positif</p>
          <p className="text-3xl font-bold text-green-700 mt-1">{posList.length}</p>
        </div>
        <div className="bg-white p-5 rounded-lg shadow-sm border border-slate-200">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Netral</p>
          <p className="text-3xl font-bold text-slate-600 mt-1">{neuList.length}</p>
        </div>
        <div className="bg-white p-5 rounded-lg shadow-sm border border-red-200 bg-red-50/30">
          <p className="text-xs font-bold text-red-600 uppercase tracking-wider">Isu Negatif</p>
          <p className="text-3xl font-bold text-red-700 mt-1">{negList.length}</p>
        </div>
      </div>

      {/* WARNING SECTION (FULL WIDTH) */}
      {negList.length > 0 && (
        <div className="mb-8 bg-white rounded-lg shadow-sm border border-red-200 overflow-hidden">
          <div className="bg-red-50 px-6 py-4 border-b border-red-100 flex justify-between items-center">
            <h2 className="lg font-bold text-red-800 flex items-center gap-2">
              PERINGATAN DINI (ISU NEGATIF)
            </h2>
            <span className="text-xs font-semibold bg-red-200 text-red-800 px-2 py-1 rounded-full">
              {negList.length} Isu Terdeteksi
            </span>
          </div>
          <div className="divide-y divide-slate-100">
            {negList.map((item: any) => (
              <div key={item.id} className="p-5 hover:bg-red-50/10 transition-colors">
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <h3 className="font-bold text-slate-800 text-lg leading-snug">{item.title}</h3>
                    <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                      <span className="flex items-center gap-1">
                        {item.published_date}
                      </span>
                      <span className="flex items-center gap-1 font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                        {item.media_name}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600 mt-3 line-clamp-2 leading-relaxed">
                      {item.content}
                    </p>
                  </div>
                  <a 
                    href={item.url} 
                    target="_blank" 
                    className="shrink-0 text-xs font-bold text-blue-600 border border-blue-200 px-3 py-1.5 rounded hover:bg-blue-50 transition"
                  >
                    Buka &rarr;
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* DATA TABLE */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
          <h3 className="font-bold text-slate-700">Arsip Berita Terkini</h3>
          <span className="text-xs font-medium text-slate-500 bg-white px-2 py-1 rounded border border-slate-200">
            Menampilkan {data.length} data
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500 border-b border-slate-200 uppercase text-xs tracking-wider">
              <tr>
                <th className="px-6 py-3 font-semibold w-32">Tanggal</th>
                <th className="px-6 py-3 font-semibold w-32">Media</th>
                <th className="px-6 py-3 font-semibold">Judul</th>
                <th className="px-6 py-3 font-semibold w-32 text-center">Sentimen</th>
                <th className="px-6 py-3 font-semibold w-24 text-center">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((item: any) => (
                <tr key={item.id} className="hover:bg-slate-50 transition-colors group">
                  <td className="px-6 py-4 text-slate-500 whitespace-nowrap">{item.published_date}</td>
                  <td className="px-6 py-4 font-medium text-slate-600">{item.media_name}</td>
                  <td className="px-6 py-4 font-medium text-slate-800 leading-snug group-hover:text-blue-700 transition-colors">
                    {item.title}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`inline-block px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wide border ${
                      item.sentiment_label === 'Negatif' ? 'bg-red-50 text-red-700 border-red-200' :
                      item.sentiment_label === 'Positif' ? 'bg-green-50 text-green-700 border-green-200' :
                      'bg-slate-100 text-slate-600 border-slate-200'
                    }`}>
                      {item.sentiment_label}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <a 
                      href={item.url} 
                      target="_blank" 
                      className="text-slate-400 hover:text-blue-600 transition-colors"
                      title="Buka Link"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 mx-auto">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                      </svg>
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}