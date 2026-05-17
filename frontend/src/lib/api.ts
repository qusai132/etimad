import type { Tender, TenderList, TenderFilters } from "@/types/tender";

const API_BASE = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1`
  : "/api/v1";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchTenders(filters: TenderFilters): Promise<TenderList> {
  const params = new URLSearchParams();
  params.set("page", String(filters.page));
  params.set("page_size", String(filters.page_size));
  if (filters.search) params.set("search", filters.search);
  if (filters.is_relevant !== undefined) params.set("is_relevant", String(filters.is_relevant));
  if (filters.notification_sent !== undefined)
    params.set("notification_sent", String(filters.notification_sent));
  if (filters.entity) params.set("entity", filters.entity);
  if (filters.activity) params.set("activity", filters.activity);

  return apiFetch<TenderList>(`/tenders?${params.toString()}`);
}

export async function fetchTender(id: number): Promise<Tender> {
  return apiFetch<Tender>(`/tenders/${id}`);
}

export async function triggerScrape(): Promise<{ status: string; message: string }> {
  return apiFetch("/scrape/run", { method: "POST" });
}

export async function triggerMatching(): Promise<{ status: string; message: string }> {
  return apiFetch("/matching/run", { method: "POST" });
}

export async function fetchJobsStatus(): Promise<{
  scrape_running: boolean;
  matching_running: boolean;
}> {
  return apiFetch("/jobs/status");
}
