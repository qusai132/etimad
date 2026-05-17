"use client";
import { use } from "react";
import useSWR from "swr";
import { fetchTender } from "@/lib/api";
import { formatDate, formatScore, formatPrice } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowRight, ExternalLink } from "lucide-react";
import Link from "next/link";

export default function TenderDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: tender, isLoading, error } = useSWR(
    `tender-${id}`,
    () => fetchTender(Number(id))
  );

  if (isLoading) return <div className="p-8 text-center text-muted-foreground">جارٍ التحميل...</div>;
  if (error) return <div className="p-8 text-center text-red-600">خطأ: {error.message}</div>;
  if (!tender) return null;

  return (
    <div className="min-h-screen bg-background" dir="rtl">
      <header className="bg-primary text-primary-foreground px-6 py-3 flex items-center gap-3">
        <Link href="/" className="opacity-75 hover:opacity-100">
          <ArrowRight className="h-5 w-5" />
        </Link>
        <h1 className="text-lg font-semibold">تفاصيل المنافسة</h1>
      </header>

      <div className="max-w-3xl mx-auto p-6 space-y-6">
        <div className="bg-white rounded-lg border p-6">
          <p className="text-xs text-muted-foreground mb-1">{tender.reference_number}</p>
          <h2 className="text-xl font-bold mb-4">{tender.title}</h2>

          {tender.is_relevant !== null && (
            <div className={`rounded-lg p-4 mb-6 ${tender.is_relevant ? "bg-green-50 border border-green-200" : "bg-gray-50 border"}`}>
              <div className="flex items-center justify-between">
                <span className="font-medium">{tender.is_relevant ? "✅ مناسبة لشركتك" : "❌ غير مناسبة"}</span>
                <Badge variant={tender.is_relevant ? "success" : "outline"}>{formatScore(tender.relevance_score)}</Badge>
              </div>
              {tender.relevance_reason && <p className="text-sm text-muted-foreground mt-2">{tender.relevance_reason}</p>}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 text-sm">
            {[
              ["الجهة الحكومية", tender.entity],
              ["النشاط", tender.activity],
              ["نوع المنافسة", tender.tender_type],
              ["الموقع", tender.location],
              ["تاريخ النشر", formatDate(tender.publish_date)],
              ["آخر موعد للاستفسار", formatDate(tender.last_enquiry_date)],
              ["آخر موعد للعروض", formatDate(tender.last_offer_date)],
              ["تاريخ الترسية", formatDate(tender.award_date)],
              ["سعر الوثائق", formatPrice(tender.document_price, tender.document_price_currency)],
            ].map(([label, value]) =>
              value ? (
                <div key={label as string}>
                  <div className="text-xs text-muted-foreground">{label}</div>
                  <div className="font-medium mt-0.5">{value}</div>
                </div>
              ) : null
            )}
          </div>

          {tender.tender_details && (
            <div className="mt-6 pt-4 border-t">
              <h3 className="font-medium mb-2">وصف المنافسة</h3>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">{tender.tender_details}</p>
            </div>
          )}

          {tender.details_url && (
            <div className="mt-6">
              <Button asChild>
                <a href={tender.details_url} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-4 w-4 ml-2" />
                  عرض على منصة اعتماد
                </a>
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
