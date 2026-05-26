/**
 * Composants d'étape du wizard. Chacun reçoit le contexte du wizard
 * (donnée accumulée + handlers) et rend son formulaire.
 */

import { useState } from "react";
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
  return (
    <div className="space-y-4">
      <Input
        label="Nom de l'école *"
        value={value.name}
        onChange={(e) => onChange({ ...value, name: e.target.value })}
        placeholder="AMIT Bar Ilan Netanya"
      />
      <Input
        label="Code court *"
        value={value.code}
        onChange={(e) => onChange({ ...value, code: e.target.value.toLowerCase() })}
        placeholder="amit-netanya"
        hint="Identifiant unique en URL-friendly (kebab-case)"
      />
      <Select
        label="Langue par défaut"
        value={value.default_language}
        onChange={(e) => onChange({ ...value, default_language: e.target.value })}
        options={[
          { value: "fr", label: "Français" },
          { value: "he", label: "עברית" },
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
          label="Jours actifs (Dim → ...)"
          value={days}
          onChange={(e) => setDays(Math.max(1, Math.min(7, Number(e.target.value))))}
        />
        <Input
          type="number"
          min={1}
          max={15}
          label="Créneaux par jour"
          value={slotsPerDay}
          onChange={(e) =>
            setSlotsPerDay(Math.max(1, Math.min(15, Number(e.target.value))))
          }
        />
        <Input
          type="time"
          label="Heure de début"
          value={firstHour}
          onChange={(e) => setFirstHour(e.target.value)}
        />
      </div>
      <Button variant="secondary" onClick={regenerate} type="button">
        Générer la grille ({days} jours × {slotsPerDay} créneaux = {days * slotsPerDay})
      </Button>

      {slots.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-900/50">
              <tr>
                <th className="px-3 py-2 text-left">#</th>
                {Array.from({ length: days }, (_, d) => (
                  <th key={d} className="px-3 py-2 text-left">
                    {["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"][d]}
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
  addLabel = "+ Ajouter",
}: RowEditorProps<T>) {
  const updateRow = (idx: number, patch: Partial<T>) => {
    const next = [...rows];
    next[idx] = { ...next[idx], ...patch };
    onChange(next);
  };
  const removeRow = (idx: number) => {
    onChange(rows.filter((_, i) => i !== idx));
  };
  const addRow = () => onChange([...rows, { ...emptyRow(), _id: crypto.randomUUID() }]);

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 dark:bg-slate-900/50">
            <tr>
              {columns.map((c) => (
                <th key={String(c.key)} className="px-3 py-2 text-left font-medium" style={c.width ? { width: c.width } : undefined}>
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
                  Aucune ligne. Cliquez sur "{addLabel}" pour commencer.
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
                    aria-label="Supprimer"
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
        {addLabel}
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
  return (
    <RowsEditor
      rows={rows}
      onChange={onChange}
      emptyRow={() => ({ code: "", name: "", order: 7, grouping_policy: "class_centric" as GP })}
      addLabel="+ Ajouter un niveau"
      columns={[
        { key: "code", label: "Code", width: "20%" },
        { key: "name", label: "Nom" },
        { key: "order", label: "Ordre", type: "number", width: "15%" },
        {
          key: "grouping_policy",
          label: "Politique",
          type: "select",
          options: [
            { value: "class_centric", label: "Par classe" },
            { value: "group_centric", label: "Par groupe" },
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
  grade_id: number | string; // string venant du <select>, converti à l'envoi
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
  return (
    <RowsEditor
      rows={rows}
      onChange={onChange}
      emptyRow={() => ({ code: "", name: "", student_count: 25, grade_id: "" })}
      addLabel="+ Ajouter une classe"
      columns={[
        { key: "code", label: "Code (ex: 7-1)" },
        { key: "name", label: "Nom" },
        { key: "student_count", label: "Élèves", type: "number", width: "15%" },
        {
          key: "grade_id",
          label: "Niveau",
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
  return (
    <RowsEditor
      rows={rows}
      onChange={onChange}
      emptyRow={() => ({ code: "", name_fr: "", name_he: "", color_hex: "", required_room_type: "" })}
      addLabel="+ Ajouter une matière"
      columns={[
        { key: "code", label: "Code", width: "15%" },
        { key: "name_fr", label: "Nom FR" },
        { key: "name_he", label: "Nom HE" },
        { key: "color_hex", label: "Couleur (#hex)", width: "15%" },
        { key: "required_room_type", label: "Salle requise", width: "15%" },
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
  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-600 dark:text-slate-400">
        <strong>Langues</strong> : liste séparée par virgules (ex: <code>fr,he</code>).{" "}
        <strong>Matières</strong> : codes séparés par virgules parmi{" "}
        {subjects.map((s) => s.code).join(", ") || "(aucune définie à l'étape précédente)"}.
      </p>
      <RowsEditor
        rows={rows}
        onChange={onChange}
        emptyRow={() => ({
          code: "",
          first_name: "",
          last_name: "",
          email: "",
          languages: "fr,he",
          qualified_subject_codes: "",
        })}
        addLabel="+ Ajouter un prof"
        columns={[
          { key: "code", label: "Code", width: "12%" },
          { key: "first_name", label: "Prénom" },
          { key: "last_name", label: "Nom" },
          { key: "email", label: "Email" },
          { key: "languages", label: "Langues", width: "12%" },
          { key: "qualified_subject_codes", label: "Matières (codes)", width: "20%" },
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
  return (
    <RowsEditor
      rows={rows}
      onChange={onChange}
      emptyRow={() => ({ code: "", name: "", capacity: 30, room_type: "" })}
      addLabel="+ Ajouter une salle"
      columns={[
        { key: "code", label: "Code", width: "20%" },
        { key: "name", label: "Nom" },
        { key: "capacity", label: "Capacité", type: "number", width: "15%" },
        { key: "room_type", label: "Type", width: "20%" },
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
  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-600 dark:text-slate-400">
        Un Group = un cours réel placé dans la grille (matière × prof(s) × classe(s)).{" "}
        <strong>Profs / classes</strong> : codes séparés par virgules. Pour une{" "}
        <strong>barrette</strong> (math 5/3 yehidot), créez 2+ Groups avec les mêmes
        source_classes et même grade.
      </p>
      <RowsEditor
        rows={rows}
        onChange={onChange}
        emptyRow={() => ({
          label: "",
          grade_id: "",
          subject_code: subjects[0]?.code ?? "",
          hours_per_week: 2,
          group_type: "whole_class" as GT,
          teacher_codes: "",
          source_class_codes: "",
        })}
        addLabel="+ Ajouter un groupe"
        columns={[
          { key: "label", label: "Libellé" },
          {
            key: "grade_id",
            label: "Niveau",
            type: "select",
            options: [
              { value: "", label: "—" },
              ...grades.map((g) => ({ value: g.id, label: g.code })),
            ],
            width: "10%",
          },
          {
            key: "subject_code",
            label: "Matière",
            type: "select",
            options: subjects.map((s) => ({ value: s.code, label: s.code })),
            width: "12%",
          },
          { key: "teacher_codes", label: "Profs (codes)", width: "15%" },
          { key: "source_class_codes", label: "Classes (codes)", width: "15%" },
          { key: "hours_per_week", label: "h/sem", type: "number", width: "10%" },
          {
            key: "group_type",
            label: "Type",
            type: "select",
            options: [
              { value: "whole_class", label: "Classe entière" },
              { value: "level_group", label: "Niveau" },
              { value: "option_group", label: "Option" },
              { value: "gender_group", label: "Genre" },
              { value: "split_group", label: "Dédoublement" },
            ],
            width: "15%",
          },
        ]}
      />
      <p className="text-xs text-slate-500 dark:text-slate-400">
        Profs disponibles :{" "}
        {teachers.map((t) => `${t.code}`).join(", ") || "(aucun)"}.<br />
        Classes disponibles :{" "}
        {classes.map((c) => c.code).join(", ") || "(aucune)"}.
      </p>
    </div>
  );
}
