"use client";
import { useEffect, useState } from "react";
import { fetchTenders, triggerScrape, triggerMatching, fetchJobsStatus } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, Zap, Bell } from "lucide-react";

interface Stats {
  total: number;
  relevant: number;
  notified: number;
}

export function StatsBar({ onRefresh }: { onRefresh: () => void }) {
  const [stats, setStats] = useState<Stats>({ total: 0, relevant: 0, notified: 0 });
  const [jobsStatus, setJobsStatus] = useState({ scrape_running: false, matching_running: false });
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      const [all, relevant, notified, status] = await Promise.all([
        fetchTenders({ page: 1, page_size: 1 }),
        fetchTenders({ page: 1, page_size: 1, is_relevant: true }),
        fetchTenders({ page: 1, page_size: 1, notification_sent: true }),
        fetchJobsStatus(),
      ]);
      setStats({ total: all.total, relevant: relevant.total, notified: notified.total });
      setJobsStatus(status);
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleScrape = async () => {
    try {
      const r = await triggerScrape();
      setMessage(r.message);
      setTimeout(() => { setMessage(null); onRefresh(); }, 3000);
    } catch (e: unknown) {
      setMessage(e instanceof Error ? e.message : "خطأ في تشغيل جلب البيانات");
    }
  };

  const handleMatch = async () => {
    try {
      const r = await triggerMatching();
      setMessage(r.message);
      setTimeout(() => { setMessage(null); onRefresh(); }, 3000);
    } catch (e: unknown) {
      setMessage(e instanceof Error ? e.message : "خطأ في تشغيل المطابقة");
    }
  };

  return (
    <div className="bg-white border-b px-6 py-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-primary">{stats.total.toLocaleString("ar-SA")}</div>
            <div className="text-xs text-muted-foreground">إجمالي المناقصات</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{stats.relevant.toLocaleString("ar-SA")}</div>
            <div className="text-xs text-muted-foreground">المناسبة لشركتك</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{stats.notified.toLocaleString("ar-SA")}</div>
            <div className="text-xs text-muted-foreground">تم إرسال الإشعار</div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {message && (
            <Badge variant="secondary" className="text-xs">{message}</Badge>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={handleScrape}
            disabled={jobsStatus.scrape_running}
          >
            <RefreshCw className={`h-4 w-4 ml-1 ${jobsStatus.scrape_running ? "animate-spin" : ""}`} />
            {jobsStatus.scrape_running ? "جارٍ الجلب..." : "جلب المناقصات"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleMatch}
            disabled={jobsStatus.matching_running}
          >
            <Zap className="h-4 w-4 ml-1" />
            {jobsStatus.matching_running ? "جارٍ المطابقة..." : "تشغيل المطابقة"}
          </Button>
        </div>
      </div>
    </div>
  );
}
