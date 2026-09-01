import { useLang, Lang } from "@/lib/i18n";

const OPTIONS: { value: Lang; label: string }[] = [
  { value: "en", label: "English" },
  { value: "ko", label: "한국어" },
];

export function LanguageToggle() {
  const { lang, setLang } = useLang();
  return (
    <div
      className="inline-flex rounded-md border border-border overflow-hidden"
      role="tablist"
      aria-label="Language"
    >
      {OPTIONS.map((o) => (
        <button
          key={o.value}
          role="tab"
          aria-selected={lang === o.value}
          onClick={() => setLang(o.value)}
          className={`px-3 py-1.5 text-sm font-medium transition-colors ${
            lang === o.value
              ? "bg-primary text-primary-foreground"
              : "bg-card text-muted-foreground hover:bg-accent"
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
