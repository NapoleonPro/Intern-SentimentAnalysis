'use client';
import { useState, useMemo } from 'react';
import Link from 'next/link';
interface Article {
  id: number;
  title: string;
  content: string;
  url: string;
  published_date: string;
  created_at: string;
  sentiment_label: string;
  sentiment_score: number;
  media_name: string;
}
interface DashboardClientProps {
  initialData: Article[];
}
export default function DashboardClient({ initialData = [] }: DashboardClientProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSentiment, setFilterSentiment] = useState('Semua');
  const [filterMedia, setFilterMedia] = useState('Semua');
  const lastUpdated = useMemo(() => {
    if (!initialData || initialData.length === 0) {
      return null;
    }
    
    const dateNumbers = initialData
      .map(article => new Date(article.created_at).getTime())
      .filter(t => !isNaN(t));
    if (dateNumbers.length === 0) {
        return null;
    }
    const latestDate = new Date(Math.max(...dateNumbers));
    return latestDate.toLocaleString('id-ID', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
  }, [initialData]);
  const filteredData = useMemo(() => {
    return initialData.filter(item => {
      const matchSearch = item.title.toLowerCase().includes(searchTerm.toLowerCase());
      const matchSentiment = filterSentiment === 'Semua' || item.sentiment_label === filterSentiment;
      const matchMedia = filterMedia === 'Semua' || item.media_name === filterMedia;
      return matchSearch && matchSentiment && matchMedia;
    });
  }, [initialData, searchTerm, filterSentiment, filterMedia]);
  const stats = useMemo(() => {
    const total = initialData.length;
    const negative = initialData.filter(x => x.sentiment_label === 'Negatif').length;
    const positive = initialData.filter(x => x.sentiment_label === 'Positif').length;
    const neutral = initialData.filter(x => x.sentiment_label === 'Netral').length;
    return { total, negative, positive, neutral };
  }, [initialData]);
  const uniqueMedia = useMemo(() => {
    return ['Semua', ...Array.from(new Set(initialData.map(item => item.media_name)))];
  }, [initialData]);
  const negativeList = useMemo(() => {
    return initialData.filter(x => x.sentiment_label === 'Negatif');
  }, [initialData]);
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-50 to-blue-50 flex flex-col">
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200/60 sticky top-0 z-50">
        <div className="w-full px-8 py-5">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6 text-white">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                  Dashboard EWS
                </h1>
                <p className="text-sm text-slate-500">Sistem Peringatan Dini Opini Publik - Pemerintah Aceh</p>
              </div>
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-500 bg-slate-100/80 px-4 py-2 rounded-lg">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {lastUpdated ? (
                <span className="font-medium">Update Terakhir: {lastUpdated}</span>
              ) : (
                <span className="font-medium">Belum ada data</span>
              )}
            </div>
          </div>
        </div>
      </header>
      <main className="flex-1 w-full px-8 py-8 overflow-y-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
          <div 
            onClick={() => document.getElementById('arsip-berita')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
            className="bg-white border-0 rounded-xl shadow-sm shadow-slate-200/50 hover:shadow-md transition-all duration-300 p-6 cursor-pointer hover:scale-[1.02]"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Total Berita</p>
                <p className="text-4xl font-bold text-slate-800">{stats.total}</p>
              </div>
              <div className="w-14 h-14 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-2xl flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-7 h-7 text-blue-600">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z" />
                </svg>
              </div>
            </div>
          </div>
          <div className="bg-white border-0 rounded-xl shadow-sm shadow-slate-200/50 hover:shadow-md transition-all duration-300 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-1">Positif</p>
                <p className="text-4xl font-bold text-emerald-600">{stats.positive}</p>
                <p className="text-xs text-slate-500 mt-1">
                  {stats.total > 0 ? Math.round((stats.positive / stats.total) * 100) : 0}% dari total
                </p>
              </div>
              <div className="w-14 h-14 bg-gradient-to-br from-emerald-50 to-green-100 rounded-2xl flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-7 h-7 text-emerald-600">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
                </svg>
              </div>
            </div>
          </div>
          <div className="bg-white border-0 rounded-xl shadow-sm shadow-slate-200/50 hover:shadow-md transition-all duration-300 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Netral</p>
                <p className="text-4xl font-bold text-slate-600">{stats.neutral}</p>
                <p className="text-xs text-slate-500 mt-1">
                  {stats.total > 0 ? Math.round((stats.neutral / stats.total) * 100) : 0}% dari total
                </p>
              </div>
              <div className="w-14 h-14 bg-gradient-to-br from-slate-50 to-slate-100 rounded-2xl flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-7 h-7 text-slate-500">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14" />
                </svg>
              </div>
            </div>
          </div>
          <div className="bg-gradient-to-br from-red-500 to-rose-600 border-0 rounded-xl shadow-lg shadow-red-500/20 hover:shadow-xl hover:shadow-red-500/30 transition-all duration-300 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-red-100 uppercase tracking-wider mb-1">Isu Negatif</p>
                <p className="text-4xl font-bold text-white">{stats.negative}</p>
                <p className="text-xs text-red-100 mt-1">
                  {stats.total > 0 ? Math.round((stats.negative / stats.total) * 100) : 0}% dari total
                </p>
              </div>
              <div className="w-14 h-14 bg-white/20 backdrop-blur rounded-2xl flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-7 h-7 text-white">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6L9 12.75l4.286-4.286a11.948 11.948 0 014.306 6.43l.776 2.898m0 0l3.182-5.511m-3.182 5.51l-5.511-3.181" />
                </svg>
              </div>
            </div>
          </div>
        </div>
        {negativeList.length > 0 && (
          <div className="border-0 rounded-xl shadow-lg shadow-red-500/10 mb-8 overflow-hidden">
            <div className="bg-gradient-to-r from-red-500 to-rose-500 py-4 px-6">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-white/20 backdrop-blur rounded-xl flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-white">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                    </svg>
                  </div>
                  <h2 className="text-white text-lg font-bold">Peringatan Dini - Isu Negatif</h2>
                </div>
                <span className="bg-white/20 text-white border-0 font-semibold px-3 py-1 rounded-full text-sm">
                  {negativeList.length} Isu Terdeteksi
                </span>
              </div>
            </div>
            <div className="bg-white divide-y divide-slate-100 max-h-[60vh] overflow-y-auto">
              {negativeList.map((item) => (
                <div key={item.id} className="p-3 hover:bg-slate-50/80 transition-colors">
                  <div className="flex justify-between items-start gap-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-slate-800 text-sm leading-tight mb-1.5">
                        {item.title}
                      </h3>
                      <div className="flex items-center gap-2 text-[11px] text-slate-500 mb-1.5">
                        <span className="flex items-center gap-1">
                          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3 h-3">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          {new Date(item.published_date).toLocaleDateString('id-ID', {
                            day: 'numeric', month: 'short', year: 'numeric'
                          })}
                        </span>
                        <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium text-[11px]">
                          {item.media_name}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 leading-relaxed line-clamp-2">{item.content}</p>
                    </div>
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="shrink-0 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg text-[11px] font-semibold shadow-sm transition-colors flex items-center gap-1.5"
                    >
                      Buka
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3 h-3">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                      </svg>
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        <div id="arsip-berita" className="bg-white border-0 rounded-xl shadow-sm shadow-slate-200/50">
          <div className="bg-slate-50/80 border-b border-slate-100 py-4 px-6 rounded-t-xl">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div className="flex items-center gap-3">
                <h3 className="text-lg font-bold text-slate-800">Arsip Berita Terkini</h3>
                <span className="bg-slate-200 text-slate-700 px-3 py-1 rounded-full text-xs font-semibold">
                  {filteredData.length} Data
                </span>
              </div>
              <div className="flex gap-3">
                <div className="relative">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                  </svg>
                  <input
                    type="text"
                    placeholder="Cari judul..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-52 pl-10 pr-4 h-10 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  />
                </div>
                <div className="relative">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none z-10">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 01-.659 1.591l-5.432 5.432a2.25 2.25 0 00-.659 1.591v2.927a2.25 2.25 0 01-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 00-.659-1.591L3.659 7.409A2.25 2.25 0 013 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0112 3z" />
                  </svg>
                  <select
                    value={filterSentiment}
                    onChange={(e) => setFilterSentiment(e.target.value)}
                    className="w-40 pl-9 pr-4 h-10 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm appearance-none bg-white cursor-pointer"
                  >
                    <option value="Semua">Semua Sentimen</option>
                    <option value="Positif">Positif</option>
                    <option value="Netral">Netral</option>
                    <option value="Negatif">Negatif</option>
                  </select>
                </div>
                <select
                  value={filterMedia}
                  onChange={(e) => setFilterMedia(e.target.value)}
                  className="w-44 px-4 h-10 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm appearance-none bg-white cursor-pointer"
                >
                  {uniqueMedia.map(media => (
                    <option key={media} value={media}>{media}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
          
          {filteredData.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 h-[80vh] overflow-y-auto">
              {filteredData.map((item) => (
                <div key={item.id} className="bg-white border border-slate-100 rounded-lg shadow-sm hover:shadow-md transition-all duration-300 h-fit">
                  <div className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium text-[11px]">
                        {item.media_name}
                      </span>
                      <span className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-bold uppercase ${
                        item.sentiment_label === 'Negatif' ? 'bg-red-100 text-red-700' :
                        item.sentiment_label === 'Positif' ? 'bg-emerald-100 text-emerald-700' :
                        'bg-slate-100 text-slate-600'
                      }`}>
                        {item.sentiment_label}
                      </span>
                    </div>
                    <h3 className="font-bold text-slate-800 text-sm leading-tight mb-2 hover:text-blue-700 transition-colors">
                      {item.title}
                    </h3>
                  </div>
                  <div className="border-t border-slate-100 bg-slate-50/50 px-4 py-2 flex justify-between items-center rounded-b-lg">
                    <span className="text-[11px] text-slate-500 font-medium">
                      {new Date(item.published_date).toLocaleDateString('id-ID', {
                        day: 'numeric', month: 'long', year: 'numeric'
                      })}
                    </span>
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-slate-500 hover:bg-blue-100 hover:text-blue-600 transition-colors"
                      title="Buka Link"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3.5 h-3.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                      </svg>
                    </a>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-20 text-center">
              <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8 text-slate-400">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                </svg>
              </div>
              <p className="text-slate-600 font-semibold text-lg">Tidak ada data yang sesuai</p>
              <p className="text-slate-400 text-sm mt-1">Coba ubah kriteria filter Anda</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}