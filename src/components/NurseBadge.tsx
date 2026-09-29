import { useLang } from "@/lib/i18n";

/**
 * Marks a nurse who is not regular permanent staff.
 *
 * "temp" is a real temp nurse with a contract window. "phantom" is a temp the
 * optimizer invented for a what-if variant, which has no database row until the
 * manager applies that schedule - worth distinguishing, because a phantom is a
 * hiring proposal rather than a colleague.
 *
 * Shares the pill shape with the invite-status badge in NursesPanel.
 */
export function NurseBadge({ kind }: { kind?: "temp" | "phantom" }) {
  const { t } = useLang();
  if (!kind) return null;
  const tone =
    kind === "phantom"
      ? "bg-primary/10 text-primary border border-dashed border-primary/50"
      : "bg-sky-100 text-sky-700";
  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide ${tone}`}
    >
      {kind === "phantom" ? t("nurses.badgeProposed") : t("nurses.badgeTemp")}
    </span>
  );
}
