"use client";
import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { TenderFilters } from "@/types/tender";
import { Search, X } from "lucide-react";

interface Props {
  filters: TenderFilters;
  onChange: (f: Partial<TenderFilters>) => void;
}

export function TenderFilterBar({ filters, onChange }: Props) {
  const [search, setSearch] = useState(filters.search || "");

  useEffect(() => {
    const t = setTimeout(() => onChange({ search: search || undefined, page: 1 }), 400);
    return () => clearTimeout(t);
  }, [search]);

  const reset = () => {
    setSearch("");
    onChange({ search: undefined, is_relevant: undefined, notification_sent: undefined, page: 1 });
  };

  return (
    <div className="flex flex-wrap gap-3 p-4 bg-muted/40 border-b">
      <div className="relative flex-1 min-w-[220px]">
        <Search className="absolute right-3 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="بحث في العنوان، الجهة، الرقم المرجعي..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pr-9"
        />
      </div>

      <Select
        value={filters.is_relevant === undefined ? "all" : String(filters.is_relevant)}
        onValueChange={(v) =>
          onChange({ is_relevant: v === "all" ? undefined : v === "true", page: 1 })
        }
      >
        <SelectTrigger className="w-40">
          <SelectValue placeholder="الملاءمة" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">جميع المناقصات</SelectItem>
          <SelectItem value="true">مناسبة فقط</SelectItem>
          <SelectItem value="false">غير مناسبة</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={filters.notification_sent === undefined ? "all" : String(filters.notification_sent)}
        onValueChange={(v) =>
          onChange({ notification_sent: v === "all" ? undefined : v === "true", page: 1 })
        }
      >
        <SelectTrigger className="w-44">
          <SelectValue placeholder="الإشعار" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">جميع الحالات</SelectItem>
          <SelectItem value="true">تم الإرسال</SelectItem>
          <SelectItem value="false">لم يُرسل</SelectItem>
        </SelectContent>
      </Select>

      <Button variant="ghost" size="sm" onClick={reset}>
        <X className="h-4 w-4 ml-1" />
        مسح
      </Button>
    </div>
  );
}
