"use client";
import { useState, useCallback } from "react";
import useSWR from "swr";
import { fetchTenders } from "@/lib/api";
import type { TenderFilters, Tender } from "@/types/tender";
import { StatsBar } from "@/components/dashboard/StatsBar";
import { TenderFilterBar } from "@/components/dashboard/TenderFilters";
import { TenderTable } from "@/components/dashboard/TenderTable";
import { TenderDrawer } from "@/components/dashboard/TenderDrawer";

const DEFAULT_FILTERS: TenderFilters = { page: 1, page_size: 20 };

export default function DashboardPage() {
  const [filters, setFilters] = useState<TenderFilters>(DEFAULT_FILTERS);
  const [selected, setSelected] = useState<Tender | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const { data, isLoading, error } = useSWR(
    [filters, refreshKey],
    ([f]) => fetchTenders(f),
    { keepPreviousData: true, refreshInterval: 60000 }
  );

  const handleFilterChange = useCallback((partial: Partial<TenderFilters>) => {
    setFilters((prev) => ({ ...prev, ...partial }));
  }, []);

  const handleRefresh = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  return (
    <div className="flex flex-col h-screen bg-background" dir="rtl">
      {/* Header */}
      <header className="bg-primary text-primary-foreground px-6 py-3 flex items-center gap-3">
        <div className="flex flex-col">
          <h1 className="text-lg font-bold leading-tight">مراقب مناقصات اعتماد</h1>
          <p className="text-xs opacity-75">رصد وتحليل مناقصات منصة اعتماد السعودية</p>
        </div>
      </header>

      <StatsBar onRefresh={handleRefresh} />
      <TenderFilterBar filters={filters} onChange={handleFilterChange} />

      <main className="flex-1 overflow-hidden">
        {error && (
          <div className="p-4 text-red-600 text-sm">خطأ في تحميل البيانات: {error.message}</div>
        )}
        {isLoading && !data && (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            جارٍ التحميل...
          </div>
        )}
        {data && (
          <TenderTable
            data={data.items}
            total={data.total}
            page={data.page}
            pages={data.pages}
            onPageChange={(p) => handleFilterChange({ page: p })}
            onRowClick={setSelected}
          />
        )}
      </main>

      <TenderDrawer tender={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
