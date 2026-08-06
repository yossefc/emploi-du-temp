/**
 * Vue grille d'un planning : (jour, créneau) → cours placés.
 *
 * Deux modes :
 * - filtré (par classe ou par prof) : la vue lisible, une case = un cours
 * - global : toutes les classes, utile seulement pour un survol
 */

import { useTranslation } from "react-i18next";
import type { Group, ScheduleEntry, Subject, Teacher, TimeSlot } from "@/lib/types";

interface Props {
  entries: ScheduleEntry[];
  groups: Group[];
  subjects: Subject[];
  timeSlots: TimeSlot[];
  teachers?: Teacher[];
  /** N'afficher que les cours de cette classe */
  filterClassId?: number | null;
  /** N'afficher que les cours de ce prof */
  filterTeacherId?: number | null;
}

const DAY_LABELS_FR = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];
const DAY_LABELS_HE = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"];

/** Noir ou blanc selon la luminance du fond — pour que le texte reste lisible. */
function textOn(hex: string): string {
  const h = hex.replace("#", "");
  if (h.length !== 6) return "#fff";
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.6 ? "#1e293b" : "#ffffff";
}

export function TimetableGrid({
  entries,
  groups,
  subjects,
  timeSlots,
  teachers,
  filterClassId,
  filterTeacherId,
}: Props) {
  const { i18n, t } = useTranslation();
  const isHe = i18n.language === "he";
  const DAY_LABELS = isHe ? DAY_LABELS_HE : DAY_LABELS_FR;

  const days = Array.from(new Set(timeSlots.map((s) => s.day_of_week))).sort();
  const slotsPerDay = Math.max(0, ...timeSlots.map((s) => s.slot_index)) + 1;

  const groupById = new Map(groups.map((g) => [g.id, g]));
  const subjectById = new Map(subjects.map((s) => [s.id, s]));
  const teacherById = new Map((teachers ?? []).map((tt) => [tt.id, tt]));

  const visible = entries.filter((e) => {
    const g = groupById.get(e.group_id);
    if (!g) return false;
    if (filterClassId != null && !g.source_class_ids.includes(filterClassId)) return false;
    if (filterTeacherId != null && !g.teacher_ids.includes(filterTeacherId)) return false;
    return true;
  });

  const cells = new Map<string, ScheduleEntry[]>();
  for (const e of visible) {
    const key = `${e.day_of_week}-${e.slot_index}`;
    cells.set(key, [...(cells.get(key) ?? []), e]);
  }

  const slotTimes = new Map<number, { start: string; end: string }>();
  for (const ts of timeSlots) {
    if (ts.is_active && !ts.is_break && !slotTimes.has(ts.slot_index)) {
      slotTimes.set(ts.slot_index, {
        start: ts.start_time.slice(0, 5),
        end: ts.end_time.slice(0, 5),
      });
    }
  }

  const isFiltered = filterClassId != null || filterTeacherId != null;

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
      <table className="min-w-full text-sm border-collapse">
        <thead className="bg-slate-100 dark:bg-slate-900/60">
          <tr>
            <th className="px-3 py-2 text-center font-medium text-slate-600 dark:text-slate-300 w-20 border-b border-slate-200 dark:border-slate-700">
              {t("schedules.slot_label", { defaultValue: isHe ? "שעה" : "Créneau" })}
            </th>
            {days.map((d) => (
              <th
                key={d}
                className="px-3 py-2 text-center font-semibold text-slate-700 dark:text-slate-200 min-w-[150px] border-b border-s border-slate-200 dark:border-slate-700"
              >
                {DAY_LABELS[d]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: slotsPerDay }, (_, slotIdx) => (
            <tr key={slotIdx} className="border-t border-slate-200 dark:border-slate-700">
              <td className="px-2 py-2 text-center font-semibold text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-900/40 align-middle">
                <div>{slotIdx + 1}</div>
                {slotTimes.get(slotIdx) && (
                  <div className="text-[10px] text-slate-400 font-normal leading-tight">
                    {slotTimes.get(slotIdx)!.start}
                  </div>
                )}
              </td>
              {days.map((d) => {
                const cellEntries = cells.get(`${d}-${slotIdx}`) ?? [];
                return (
                  <td
                    key={d}
                    className="p-1 align-top border-s border-slate-200 dark:border-slate-700"
                  >
                    {cellEntries.length === 0 ? (
                      <div className="h-10" />
                    ) : (
                      <div className="space-y-1">
                        {cellEntries.map((e) => {
                          const g = groupById.get(e.group_id)!;
                          const subj = subjectById.get(g.subject_id);
                          const bg = subj?.color_hex ?? "#94a3b8";
                          const fg = textOn(bg);
                          const profNames = g.teacher_ids
                            .map((id) => teacherById.get(id)?.first_name)
                            .filter(Boolean)
                            .join(", ");
                          return (
                            <div
                              key={e.id}
                              className="rounded-md px-2 py-1 leading-tight shadow-sm"
                              style={{ backgroundColor: bg, color: fg }}
                              title={`${g.label}${profNames ? " — " + profNames : ""}`}
                            >
                              <div className="font-semibold text-xs truncate">
                                {subj?.name_he ?? subj?.code}
                              </div>
                              {isFiltered && profNames && (
                                <div className="text-[10px] opacity-90 truncate">
                                  {profNames}
                                </div>
                              )}
                              {!isFiltered && (
                                <div className="text-[10px] opacity-90 truncate">
                                  {g.label}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
