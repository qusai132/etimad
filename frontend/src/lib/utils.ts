import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  try {
    return new Date(dateStr).toLocaleDateString("ar-SA", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export function formatScore(score: number | null): string {
  if (score === null || score === undefined) return "—";
  return `${Math.round(score * 100)}%`;
}

export function formatPrice(price: number | null, currency?: string | null): string {
  if (!price) return "—";
  return `${price.toLocaleString("ar-SA")} ${currency || "SAR"}`;
}
