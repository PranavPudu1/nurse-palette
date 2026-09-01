import { ChevronLeft, ChevronRight } from "lucide-react";
import { useLang, monthLabel } from "@/lib/i18n";

interface MonthSelectorProps {
  year: number;
  month: number;
  onPrev: () => void;
  onNext: () => void;
}

export function MonthSelector({ year, month, onPrev, onNext }: MonthSelectorProps) {
  const { lang, t } = useLang();
  return (
    <div className="flex items-center gap-3">
      <button
        onClick={onPrev}
        className="p-1.5 rounded-md hover:bg-accent transition-colors"
        aria-label={t("month.prev")}
      >
        <ChevronLeft className="w-5 h-5" />
      </button>
      <span className="text-lg font-semibold min-w-[180px] text-center">
        {monthLabel(lang, year, month)}
      </span>
      <button
        onClick={onNext}
        className="p-1.5 rounded-md hover:bg-accent transition-colors"
        aria-label={t("month.next")}
      >
        <ChevronRight className="w-5 h-5" />
      </button>
    </div>
  );
}
