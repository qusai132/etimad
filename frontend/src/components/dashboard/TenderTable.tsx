"use client";
import { useMemo } from "react";
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
  type ColumnDef,
} from "@tanstack/react-table";
import type { Tender } from "@/types/tender";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate, formatScore, formatPrice } from "@/lib/utils";
import { ExternalLink, Mail, CheckCircle } from "lucide-react";

const col = createColumnHelper<Tender>();

interface Props {
  data: Tender[];
  total: number;
  page: number;
  pages: number;
  onPageChange: (p: number) => void;
  onRowClick: (t: Tender) => void;
}

function RelevanceBadge({ score, isRelevant }: { score: number | null; isRelevant: boolean | null }) {
  if (isRelevant === null) return <Badge variant="outline">لم يُحلَّل</Badge>;
  if (isRelevant)
    return (
      <Badge variant="success">
        مناسبة {score !== null ? `(${Math.round(score * 100)}%)` : ""}
      </Badge>
    );
  return <Badge variant="outline" className="text-gray-400">غير مناسبة</Badge>;
}

export function TenderTable({ data, total, page, pages, onPageChange, onRowClick }: Props) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const columns = useMemo<ColumnDef<Tender, any>[]>(
    () => [
      col.accessor("reference_number", {
        header: "الرقم المرجعي",
        cell: (info) => (
          <span className="font-mono text-xs text-primary">{info.getValue() as string}</span>
        ),
        size: 120,
      }),
      col.accessor("title", {
        header: "عنوان المنافسة",
        cell: (info) => (
          <button
            onClick={() => onRowClick(info.row.original)}
            className="text-right text-sm font-medium hover:text-primary hover:underline line-clamp-2 max-w-xs"
          >
            {info.getValue() as string}
          </button>
        ),
      }),
      col.accessor("entity", {
        header: "الجهة",
        cell: (info) => (
          <span className="text-sm text-muted-foreground line-clamp-1 max-w-[150px]">
            {(info.getValue() as string) || "—"}
          </span>
        ),
      }),
      col.accessor("activity", {
        header: "النشاط",
        cell: (info) => (
          <span className="text-sm">{(info.getValue() as string) || "—"}</span>
        ),
      }),
      col.accessor("publish_date", {
        header: "تاريخ النشر",
        cell: (info) => <span className="text-sm">{formatDate(info.getValue() as string)}</span>,
      }),
      col.accessor("last_offer_date", {
        header: "آخر موعد",
        cell: (info) => <span className="text-sm">{formatDate(info.getValue() as string)}</span>,
      }),
      col.accessor("document_price", {
        header: "سعر الوثائق",
        cell: (info) => (
          <span className="text-sm">
            {formatPrice(info.getValue() as number | null, info.row.original.document_price_currency)}
          </span>
        ),
      }),
      col.display({
        id: "relevance",
        header: "الملاءمة",
        cell: (info) => (
          <RelevanceBadge
            score={info.row.original.relevance_score}
            isRelevant={info.row.original.is_relevant}
          />
        ),
      }),
      col.accessor("notification_sent", {
        header: "الإشعار",
        cell: (info) =>
          info.getValue() ? (
            <CheckCircle className="h-4 w-4 text-green-600 mx-auto" />
          ) : (
            <span className="text-muted-foreground text-xs">—</span>
          ),
      }),
      col.display({
        id: "actions",
        header: "",
        cell: (info) =>
          info.row.original.details_url ? (
            <a
              href={info.row.original.details_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-muted-foreground hover:text-primary"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          ) : null,
      }),
    ],
    [onRowClick]
  );

  const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel() });

  return (
    <div className="flex flex-col h-full">
      <div className="overflow-auto flex-1">
        <table className="w-full text-sm border-collapse">
          <thead className="sticky top-0 bg-muted/80 backdrop-blur z-10">
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    className="text-right px-3 py-2 font-medium text-muted-foreground border-b whitespace-nowrap"
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="border-b hover:bg-muted/30 cursor-pointer transition-colors"
                onClick={() => onRowClick(row.original)}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-2 align-top">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
            {data.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="text-center py-12 text-muted-foreground">
                  لا توجد مناقصات
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t bg-white">
          <span className="text-sm text-muted-foreground">
            إجمالي {total.toLocaleString("ar-SA")} منافسة — صفحة {page} من {pages}
          </span>
          <div className="flex gap-1">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
              السابق
            </Button>
            {Array.from({ length: Math.min(5, pages) }, (_, i) => {
              const p = Math.max(1, page - 2) + i;
              if (p > pages) return null;
              return (
                <Button
                  key={p}
                  variant={p === page ? "default" : "outline"}
                  size="sm"
                  onClick={() => onPageChange(p)}
                >
                  {p}
                </Button>
              );
            })}
            <Button variant="outline" size="sm" disabled={page >= pages} onClick={() => onPageChange(page + 1)}>
              التالي
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
