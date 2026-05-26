/**
 * Composants d'étape du wizard. Chaque sous-composant utilise useTranslation
 * pour afficher tous les labels selon la langue active (HE/FR).
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import type {
  GroupType as GT,
  GroupingPolicy as GP,
  SchoolClass,
  Subject,
  Teacher,
  Grade,
  TimeSlotInput,
} from "@/lib/types";


// ---- Step 1: School ----

export interface SchoolForm {
  code: string;
  name: string;
  default_language: string;
}

export function StepSchool({
  value,
  onChange,
}: {
  value: SchoolForm;
  onChange: (v: SchoolForm) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="space-y-4">
      <Input
        label={t("wizard.school_name")}
        value={value.name}
        onChange={(e) => onChange({ ...value, name: e.target.value })}
        placeholder="אמי״ת בר אילן נתניה"
      />
      <Input
        label={t("wizard.school_code")}
        value={value.code}
        onChange={(e) => onChange({ ...value, code: e.target.value.toLowerCase() })}
        placeholder="amit-netanya"
        hint={t("wizard.school_code_hint")}
      />
      <Select
        label={t("wizard.lang_default")}
        value={value.default_language}
        onChange={(e) => onChange({ ...value, default_language: e.target.value })}
        options={[
          { value: "he", label: "עברית" },
          { value: "fr", label: "Français" },
        ]}
      />
    </div>
  );
}


// ---- Step 2: TimeGrid ----

export function StepTimeGrid({
  slots,
  onChange,
}: {
  slots: TimeSlotInput[];
  onChange: (s: TimeSlotInput[]) => void;
}) {
  const { t, i18n } = useTranslation();
  const isHe = i18n.language === "he";
  const dayLabels = isHe
    ? ["א'", "ב'", "ג'", "ד'", "ה'", "ו'", "ש'"]
    : ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];

  const [days, setDays] = useState(() => {
    if (slots.length === 0) return 5;
    return new Set(slots.map((s) => s.day_of_week)).size;
  });
  const [slotsPerDay, setSlotsPerDay] = useState(() => {
    if (slots.length === 0) return 8;
    return Math.max(...slots.map((s) => s.slot_index)) + 1;
  });
  const [firstHour, setFirstHour] = useState("08:00");

  function regenerate() {
    const [h, m] = firstHour.split(":").map(Number);
    const next: TimeSlotInput[] = [];
    for (let d = 0; d < days; d++) {
      for (let i = 0; i < slotsPerDay; i++) {
        const sh = h + i;
        next.push({
          day_of_week: d,
          slot_index: i,
          start_time: `${String(sh).padStart(2, "0")}:${String(m).padStart(2, "0")}:00`,
          end_time: `${String(sh).padStart(2, "0")}:${String(m + 45).padStart(2, "0")}:00`,
          is_break: false,
          is_active: true,
          label: null,
        });
      }
    }
    onChange(next);
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Input
          type="number"
          min={1}
          max={7}
          label={t("wizard.days_active")}
          value={days}
          onChange={(e) => setDays(Math.max(1, Math.min(7, Number(e.target.value))))}
        />
        <Input
          type="number"
          min={1}
          max={15}
          label={t("wizard.slots_per_day")}
          value={slotsPerDay}
          onChange={(e) =>
            setSlotsPerDay(Math.max(1, Math.min(15, Number(e.target.value))))
          }
        />
        <Input
          type="time"
          label={t("wizard.first_hour")}
          value={firstHour}
          onChange={(e) => setFirstHour(e.target.value)}
        />
      </div>
      <Button variant="secondary" onClick={regenerate} type="button">
        {t("wizard.generate_grid", { days, slots: slotsPerDay, total: days * slotsPerDay })}
      </Button>

      {slots.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-900/50">
              <tr>
                <th className="px-3 py-2 text-start">#</th>
                {Array.from({ length: days }, (_, d) => (
                  <th key={d} className="px-3 py-2 text-start">
                    {dayLabels[d]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: slotsPerDay }, (_, i) => (
                <tr key={i} className="border-t border-slate-200 dark:border-slate-700">
                  <td className="px-3 py-2 font-medium">{i + 1}</td>
                  {Array.from({ length: days }, (_, d) => {
                    const slot = slots.find(
                      (s) => s.day_of_week === d && s.slot_index === i
                    );
                    return (
                      <td key={d} className="px-3 py-2 text-slate-500">
                        {slot
                          ? `${slot.start_time.slice(0, 5)}-${slot.end_time.slice(0, 5)}`
                          : "-"}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}


// ---- Helper : Rows editor générique ----

interface RowEditorProps<T> {
  rows: T[];
  onChange: (rows: T[]) => void;
  emptyRow: () => T;
  columns: {
    key: keyof T | string;
    label: string;
    type?: "text" | "number" | "select";
    options?: { value: string | number; label: string }[];
    width?: string;
    render?: (row: T, onUpdate: (patch: Partial<T>) => void) => React.ReactNode;
  }[];
  addLabel?: string;
}

export function RowsEditor<T extends { _id?: string }>({
  rows,
  onChange,
  emptyRow,
  columns,
  addLabel,
}: RowEditorProps<T>) {
  const { t } = useTranslation();
  const label = addLabel ?? `+ ${t("actions.create")}`;

  const updateRow = (idx: number, patch: Partial<T>) => {
    const next = [...rows];
    next[idx] = { ...next[idx], ...patch };
    onChange(next);
  };
  const removeRow = (idx: number) => onChange(rows.filter((_, i) => i !== idx));
  const addRow = () => onChange([...rows, { ...emptyRow(), _id: crypto.randomUUID() }]);

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 dark:bg-slate-900/50">
            <tr>
              {columns.map((c) => (
                <th key={String(c.key)} className="px-3 py-2 text-start font-medium" style={c.width ? { width: c.width } : undefined}>
                  {c.label}
                </th>
              ))}
              <th className="w-12" />
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan={columns.length + 1} className="px-3 py-6 text-center text-slate-500">
                  {t("wizard.cell_no_rows", { add_label: label })}
                </td>
              </tr>
            )}
            {rows.map((row, idx) => (
              <tr key={(row as any)._id ?? idx} className="border-t border-slate-200 dark:border-slate-700">
                {columns.map((c) => (
                  <td key={String(c.key)} className="px-2 py-1">
                    {c.render ? (
                      c.render(row, (patch) => updateRow(idx, patch))
                    ) : c.type === "select" ? (
                      <select
                        className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-1 text-sm"
                        value={(row[c.key as keyof T] as any) ?? ""}
                        onChange={(e) => updateRow(idx, { [c.key as keyof T]: e.target.value } as any)}
                      >
                        {c.options?.map((o) => (
                          <option key={o.value} value={o.value}>
                            {o.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type={c.type ?? "text"}
                        className="w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-2 py-1 text-sm"
                        value={(row[c.key as keyof T] as any) ?? ""}
                        onChange={(e) =>
                          updateRow(idx, {
                            [c.key as keyof T]:
                              c.type === "number" ? Number(e.target.value) : e.target.value,
                          } as any)
                        }
                      />
                    )}
                  </td>
                ))}
                <td className="px-2 py-1 text-center">
                  <button
                    type="button"
                    onClick={() => removeRow(idx)}
                    className="text-red-500 hover:text-red-700 text-lg"
                    aria-label={t("wizard.delete_row")}
                  >
                    ×
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Button variant="secondary" size="sm" onClick={addRow} type="button">
        {label}
      </Button>
    </div>
  );
}


// ---- Step 3: Grades ----

export interface GradeRow extends Record<string, unknown> {
  _id?: string;
  code: string;
  name: string;
  order: number;
  grouping_policy: GP;
}

export function StepGrades({
  rows,
  onChange,
}: {
  rows: GradeRow[];
  onChange: (r: GradeRow[]) => void;
}) {
  const { t } = useTranslation();
  return (
    <RowsEditor
      rows={rows}
      onChange={onChange}
      emptyRow={() => ({ code: "", name: "", order: 7, grouping_policy: "class_centric" as GP })}
      addLabel={t("wizard.add_grade")}
      columns={[
        { key: "code", label: t("columns.code"), width: "20%" },
        { key: "name", label: t("columns.name") },
        { key: "order", label: t("wizard.grade_order"), type: "number", width: "15%" },
        {
          key: "grouping_policy",
          label: t("wizard.grade_policy"),
          type: "select",
          options: [
            { value: "class_centric", label: t("wizard.grade_policy_class") },
            { value: "group_centric", label: t("wizard.grade_policy_group") },
          ],
        },
      ]}
    />
  );
}


// ---- Step 4: Classes ----

export interface ClassRow {
  _id?: string;
  code: string;
  name: string;
  student_count: number;
  grade_id: number | string;
}

export function StepClasses({
  rows,
  grades,
  onChange,
}: {
  rows: ClassRow[];
  grades: Grade[];
  onChange: (r: ClassRow[]) => void;
}) {
  const { t } = useTranslation();
  return (
    <RowsEditor
      rows={rows}
      onChange={onChange}
      emptyRow={() => ({ code: "", name: "", student_count: 25, grade_id: "" })}
      addLabel={t("wizard.add_class")}
      columns={[
        { key: "code", label: t("columns.code") + " (ex: " + t("wizard.class_code_hint") + ")" },
        { key: "name", label: t("columns.name") },
        { key: "student_count", label: t("columns.students"), type: "number", width: "15%" },
        {
          key: "grade_id",
          label: t("columns.grade"),
          type: "select",
          options: [
            { value: "", label: "—" },
            ...grades.map((g) => ({ value: g.id, label: g.name })),
          ],
        },
      ]}
    />
  );
}


// ---- Step 5: Subjects ----

export interface SubjectRow {
  _id?: string;
  code: string;
  name_fr: string;
  name_he: string;
  color_hex: string;
  required_room_type: string;
}

export function StepSubjects({
  rows,
  onChange,
}: {
  rows: SubjectRow[];
  onChange: (r: SubjectRow[]) => void;
}) {
  const { t } = useTranslation();
  return (
    <RowsEditor
      rows={rows}
      onChange={onChange}
      emptyRow={() => ({ code: "", name_fr: "", name_he: "", color_hex: "", required_room_type: "" })}
      addLabel={t("wizard.add_subject")}
      columns={[
        { key: "code", label: t("columns.code"), width: "15%" },
        { key: "name_he", label: "שם" },
        { key: "name_fr", label: "Nom FR" },
        { key: "color_hex", label: t("wizard.subject_color"), width: "15%" },
        { key: "required_room_type", label: t("wizard.subject_required_room"), width: "15%" },
      ]}
    />
  );
}


// ---- Step 6: Teachers ----

export interface TeacherRow {
  _id?: string;
  code: string;
  first_name: string;
  last_name: string;
  email: string;
  languages: string;
  qualified_subject_codes: string;
}

export function StepTeachers({
  rows,
  subjects,
  onChange,
}: {
  rows: TeacherRow[];
  subjects: Subject[];
  onChange: (r: TeacherRow[]) => void;
}) {
  const { t } = useTranslation();
  const codes = subjects.map((s) => s.code).join(", ") || "—";
  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-600 dark:text-slate-400">
        {t("wizard.teacher_help", { codes })}
      </p>
      <RowsEditor
        rows={rows}
        onChange={onChange}
        emptyRow={() => ({
          code: "", first_name: "", last_name: "", email: "",
          languages: "fr,he", qualified_subject_codes: "",
        })}
        addLabel={t("wizard.add_teacher")}
        columns={[
          { key: "code", label: t("columns.code"), width: "12%" },
          { key: "first_name", label: t("wizard.teacher_first_name") },
          { key: "last_name", label: t("wizard.teacher_last_name") },
          { key: "email", label: t("columns.email") },
          { key: "languages", label: t("wizard.teacher_languages"), width: "12%" },
          { key: "qualified_subject_codes", label: t("wizard.teacher_subjects"), width: "20%" },
        ]}
      />
    </div>
  );
}


// ---- Step 7: Rooms ----

export interface RoomRow {
  _id?: string;
  code: string;
  name: string;
  capacity: number;
  room_type: string;
}

export function StepRooms({
  rows,
  onChange,
}: {
  rows: RoomRow[];
  onChange: (r: RoomRow[]) => void;
}) {
  const { t } = useTranslation();
  return (
    <RowsEditor
      rows={rows}
      onChange={onChange}
      emptyRow={() => ({ code: "", name: "", capacity: 30, room_type: "" })}
      addLabel={t("wizard.add_room")}
      columns={[
        { key: "code", label: t("columns.code"), width: "20%" },
        { key: "name", label: t("columns.name") },
        { key: "capacity", label: t("wizard.room_capacity"), type: "number", width: "15%" },
        { key: "room_type", label: t("columns.type"), width: "20%" },
      ]}
    />
  );
}


// ---- Step 8: Groups ----

export interface GroupRow {
  _id?: string;
  label: string;
  grade_id: number | string;
  subject_code: string;
  hours_per_week: number;
  group_type: GT;
  teacher_codes: string;
  source_class_codes: string;
}

export function StepGroups({
  rows,
  grades,
  subjects,
  teachers,
  classes,
  onChange,
}: {
  rows: GroupRow[];
  grades: Grade[];
  subjects: Subject[];
  teachers: Teacher[];
  classes: SchoolClass[];
  onChange: (r: GroupRow[]) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-600 dark:text-slate-400">{t("wizard.group_help")}</p>
      <RowsEditor
        rows={rows}
        onChange={onChange}
        emptyRow={() => ({
          label: "", grade_id: "", subject_code: subjects[0]?.code ?? "",
          hours_per_week: 2, group_type: "whole_class" as GT,
          teacher_codes: "", source_class_codes: "",
        })}
        addLabel={t("wizard.add_group")}
        columns={[
          { key: "label", label: t("wizard.group_label") },
          {
            key: "grade_id", label: t("columns.grade"), type: "select", width: "10%",
            options: [{ value: "", label: "—" }, ...grades.map((g) => ({ value: g.id, label: g.code }))],
          },
          {
            key: "subject_code", label: t("nav.subjects"), type: "select", width: "12%",
            options: subjects.map((s) => ({ value: s.code, label: s.code })),
          },
          { key: "teacher_codes", label: t("wizard.group_teachers"), width: "15%" },
          { key: "source_class_codes", label: t("wizard.group_classes"), width: "15%" },
          { key: "hours_per_week", label: t("wizard.group_hours"), type: "number", width: "10%" },
          {
            key: "group_type", label: t("columns.type"), type: "select", width: "15%",
            options: [
              { value: "whole_class", label: t("group_type.whole_class") },
              { value: "level_group", label: t("group_type.level_group") },
              { value: "option_group", label: t("group_type.option_group") },
              { value: "gender_group", label: t("group_type.gender_group") },
              { value: "split_group", label: t("group_type.split_group") },
            ],
          },
        ]}
      />
      <p className="text-xs text-slate-500 dark:text-slate-400">
        {t("wizard.available_teachers", { names: teachers.map((t) => t.code).join(", ") || "—" })}
        <br />
        {t("wizard.available_classes", { names: classes.map((c) => c.code).join(", ") || "—" })}
      </p>
    </div>
  );
}
