/**
 * Vue grille d'un planning : (jour, créneau) → groupes placés.
 * Affichage simplifié pour le MVP.
 */

import { useTranslation } from "react-i18next";
import type { Group, ScheduleEntry, Subject, TimeSlot } from "@/lib/types";

interface Props {
  entries: ScheduleEntry[];
  groups: Group[];
  subjects: Subject[];
  timeSlots: TimeSlot[];
}

const DAY_LABELS_FR = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];
const DAY_LABELS_HE = ["א'", "ב'", "ג'", "ד'", "ה'", "ו'", "ש'"];

export function TimetableGrid({ entries, groups, subjects, timeSlots }: Props) {
  const { i18n, t } = useTranslation();
  const DAY_LABELS = i18n.language === "he" ? DAY_LABELS_HE : DAY_LABELS_FR;
  // Trouver les jours et créneaux actifs
  const days = Array.from(new Set(timeSlots.map((s) => s.day_of_week))).sort();
  const slotsPerDay = Math.max(0, ...timeSlots.map((s) => s.slot_index)) + 1;

  const groupById = new Map(groups.map((g) => [g.id, g]));
  const subjectById = new Map(subjects.map((s) => [s.id, s]));

  // Index : (day, slot) → entries
  const cells = new Map<string, ScheduleEntry[]>();
  for (const e of entries) {
    const key = `${e.day_of_week}-${e.slot_index}`;
    const list = cells.get(key) ?? [];
    list.push(e);
    cells.set(key, list);
  }

  // Index : (day, slot) → label horaire affiché
  const slotTimes = new Map<string, { start: string; end: string }>();
  for (const ts of timeSlots) {
    if (ts.is_active && !ts.is_break) {
      slotTimes.set(`${ts.day_of_week}-${ts.slot_index}`, {
        start: ts.start_time.slice(0, 5),
        end: ts.end_time.slice(0, 5),
      });
    }
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-50 dark:bg-slate-900/50 sticky top-0">
          <tr>
            <th className="px-3 py-2 text-start font-medium text-slate-600 dark:text-slate-300 sticky start-0 bg-slate-50 dark:bg-slate-900/50">
              {t("schedules.slot_label", { defaultValue: i18n.language === "he" ? "משבצת" : "Créneau" })}
            </th>
            {days.map((d) => (
              <th
                key={d}
                className="px-3 py-2 text-left font-medium text-slate-600 dark:text-slate-300 min-w-[150px]"
              >
                {DAY_LABELS[d]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: slotsPerDay }, (_, slotIdx) => (
            <tr key={slotIdx} className="border-t border-slate-200 dark:border-slate-700">
              <td className="px-3 py-2 font-medium text-slate-700 dark:text-slate-300 sticky left-0 bg-white dark:bg-slate-800 align-top">
                <div>{slotIdx + 1}</div>
                <div className="text-xs text-slate-500 font-normal">
                  {(() => {
                    const t = slotTimes.get(`${days[0]}-${slotIdx}`);
                    return t ? `${t.start}-${t.end}` : "";
                  })()}
                </div>
              </td>
              {days.map((d) => {
                const cellEntries = cells.get(`${d}-${slotIdx}`) ?? [];
                return (
                  <td key={d} className="px-2 py-2 align-top">
                    {cellEntries.length === 0 ? (
                      <span className="text-slate-300 dark:text-slate-700">—</span>
                    ) : (
                      <div className="space-y-1">
                        {cellEntries.map((e) => {
                          const g = groupById.get(e.group_id);
                          const subj = g ? subjectById.get(g.subject_id) : undefined;
                          const bg = subj?.color_hex ?? "#94a3b8";
                          return (
                            <div
                              key={e.id}
                              className="rounded px-2 py-1 text-xs text-white truncate"
                              style={{ backgroundColor: bg }}
                              title={`${g?.label} (salle #${e.room_id})`}
                            >
                              <div className="font-medium">{subj?.abbreviation ?? subj?.code}</div>
                              <div className="opacity-90">{g?.label}</div>
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
