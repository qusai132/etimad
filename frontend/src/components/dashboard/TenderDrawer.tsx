"use client";
import type { Tender } from "@/types/tender";
import { formatDate, formatScore, formatPrice } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { X, ExternalLink } from "lucide-react";

interface Props {
  tender: Tender | null;
  onClose: () => void;
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  if (!value) return null;
  return (
    <div className="mb-4">
      <div className="text-xs text-muted-foreground mb-1">{label}</div>
      <div className="text-sm">{value}</div>
    </div>
  );
}

export function TenderDrawer({ tender, onClose }: Props) {
  if (!tender) return null;

  const score = tender.relevance_score;

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black/40" onClick={onClose} />
      <div className="w-full max-w-lg bg-white shadow-xl flex flex-col h-full overflow-hidden" dir="rtl">
        <div className="flex items-start justify-between p-4 border-b bg-primary text-primary-foreground">
          <div className="flex-1 min-w-0">
            <p className="text-xs opacity-75">{tender.reference_number}</p>
            <h2 className="font-semibold text-sm leading-snug mt-0.5 line-clamp-3">{tender.title}</h2>
          </div>
          <button onClick={onClose} className="ml-2 opacity-80 hover:opacity-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {tender.is_relevant !== null && (
            <div className={`rounded-lg p-3 mb-4 ${tender.is_relevant ? "bg-green-50 border border-green-200" : "bg-gray-50 border border-gray-200"}`}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium">
                  {tender.is_relevant ? "✅ مناسبة لشركتك" : "❌ غير مناسبة"}
                </span>
                <Badge variant={tender.is_relevant ? "success" : "outline"}>
                  {formatScore(score)}
                </Badge>
              </div>
              {score !== null && (
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${tender.is_relevant ? "bg-green-500" : "bg-gray-400"}`}
                    style={{ width: `${Math.round((score || 0) * 100)}%` }}
                  />
                </div>
              )}
              {tender.relevance_reason && (
                <p className="text-xs text-muted-foreground mt-2">{tender.relevance_reason}</p>
              )}
            </div>
          )}

          <Field label="الجهة الحكومية" value={tender.entity} />
          <Field label="النشاط" value={tender.activity} />
          <Field label="نوع المنافسة" value={tender.tender_type} />
          <Field label="الموقع" value={tender.location} />

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <div className="text-xs text-muted-foreground mb-1">تاريخ النشر</div>
              <div className="text-sm">{formatDate(tender.publish_date)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">آخر موعد للاستفسار</div>
              <div className="text-sm">{formatDate(tender.last_enquiry_date)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">آخر موعد للعروض</div>
              <div className="text-sm font-medium text-red-600">{formatDate(tender.last_offer_date)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">تاريخ الترسية</div>
              <div className="text-sm">{formatDate(tender.award_date)}</div>
            </div>
          </div>

          <Field
            label="سعر الوثائق"
            value={formatPrice(tender.document_price, tender.document_price_currency)}
          />
          <Field label="وصف المنافسة" value={tender.tender_details} />
          <Field label="الغرض" value={tender.purpose} />
          <Field label="شروط التأهيل" value={tender.conditions} />
          <Field label="الكمية" value={tender.quantity} />

          <div className="mt-4 pt-4 border-t text-xs text-muted-foreground space-y-1">
            <div>تاريخ الإضافة: {formatDate(tender.created_at)}</div>
            {tender.notification_sent && (
              <div className="text-green-600">✓ تم إرسال إشعار بالبريد الإلكتروني</div>
            )}
          </div>
        </div>

        {tender.details_url && (
          <div className="p-4 border-t">
            <Button asChild className="w-full">
              <a href={tender.details_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4 ml-2" />
                عرض المنافسة على اعتماد
              </a>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
