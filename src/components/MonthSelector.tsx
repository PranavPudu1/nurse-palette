import { ChevronLeft, ChevronRight } from "lucide-react";

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

interface MonthSelectorProps {
  year: number;
  month: number;
  onPrev: () => void;
  onNext: () => void;
}

export function MonthSelector({ year, month, onPrev, onNext }: MonthSelectorProps) {
  return (
    <div className="flex items-center gap-3">
      <button
        onClick={onPrev}
        className="p-1.5 rounded-md hover:bg-accent transition-colors"
        aria-label="Previous month"
      >
        <ChevronLeft className="w-5 h-5" />
      </button>
      <span className="text-lg font-semibold min-w-[180px] text-center">
        {MONTH_NAMES[month]} {year}
      </span>
      <button
        onClick={onNext}
        className="p-1.5 rounded-md hover:bg-accent transition-colors"
        aria-label="Next month"
      >
        <ChevronRight className="w-5 h-5" />
      </button>
    </div>
  );
}
