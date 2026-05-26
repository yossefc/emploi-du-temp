/**
 * Wizard d'onboarding école : 8 étapes guidées, persistance par étape
 * (chaque "Suivant" pousse à l'API les entités créées dans cette étape).
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import { api, ApiError } from "@/lib/api";
import type {
  Grade,
  Room,
  SchoolClass,
  Subject,
  Teacher,
  TimeSlotInput,
} from "@/lib/types";
import { WizardLayout, type WizardStep } from "@/components/wizard/WizardLayout";
import {
  StepSchool,
  StepTimeGrid,
  StepGrades,
  StepClasses,
  StepSubjects,
  StepTeachers,
  StepRooms,
  StepGroups,
  type SchoolForm,
  type GradeRow,
  type ClassRow,
  type SubjectRow,
  type TeacherRow,
  type RoomRow,
  type GroupRow,
} from "@/components/wizard/steps";


const STEPS: WizardStep[] = [
  { id: "school", label: "École" },
  { id: "time-grid", label: "Grille" },
  { id: "grades", label: "Niveaux" },
  { id: "classes", label: "Classes" },
  { id: "subjects", label: "Matières" },
  { id: "teachers", label: "Profs" },
  { id: "rooms", label: "Salles" },
  { id: "groups", label: "Groupes" },
];


export default function Wizard() {
  const navigate = useNavigate();
  const qc = useQueryClient();

  // État global accumulé
  const [step, setStep] = useState(0);
  const [school, setSchool] = useState({
    id: null as number | null,
    form: { code: "", name: "", default_language: "fr" } as SchoolForm,
  });
  const [timeSlots, setTimeSlots] = useState<TimeSlotInput[]>([]);
  const [grades, setGrades] = useState<Grade[]>([]);
  const [gradeRows, setGradeRows] = useState<GradeRow[]>([]);
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [classRows, setClassRows] = useState<ClassRow[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [subjectRows, setSubjectRows] = useState<SubjectRow[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [teacherRows, setTeacherRows] = useState<TeacherRow[]>([]);
  const [, setRooms] = useState<Room[]>([]);
  const [roomRows, setRoomRows] = useState<RoomRow[]>([]);
  const [groupRows, setGroupRows] = useState<GroupRow[]>([]);

  // --- Persisters par étape (mutation TanStack) ---
  const saveStep = useMutation({
    mutationFn: async () => {
      switch (STEPS[step].id) {
        case "school": {
          if (!school.form.code.trim() || !school.form.name.trim()) {
            throw new Error("Nom et code requis");
          }
          if (school.id) {
            await api.schools.update(school.id, { name: school.form.name });
            return;
          }
          const created = await api.schools.create({
            code: school.form.code,
            name: school.form.name,
            default_language: school.form.default_language,
          });
          setSchool({ ...school, id: created.id });
          return;
        }
        case "time-grid": {
          if (!school.id) throw new Error("École non créée");
          if (timeSlots.length === 0) throw new Error("Générez d'abord la grille horaire");
          await api.schools.setTimeGrid(school.id, timeSlots);
          return;
        }
        case "grades": {
          if (!school.id) throw new Error("École non créée");
          const created: Grade[] = [];
          for (const row of gradeRows) {
            if (!row.code.trim()) continue;
            const g = await api.grades.create({
              school_id: school.id,
              code: row.code,
              name: row.name || row.code,
              order: Number(row.order) || 1,
              grouping_policy: row.grouping_policy,
            });
            created.push(g);
          }
          setGrades(created);
          return;
        }
        case "classes": {
          if (!school.id) throw new Error("École non créée");
          const created: SchoolClass[] = [];
          for (const row of classRows) {
            if (!row.code.trim() || !row.grade_id) continue;
            const c = await api.classes.create({
              school_id: school.id,
              grade_id: Number(row.grade_id),
              code: row.code,
              name: row.name || row.code,
              student_count: Number(row.student_count) || 0,
              homeroom_teacher_id: null,
            });
            created.push(c);
          }
          setClasses(created);
          return;
        }
        case "subjects": {
          if (!school.id) throw new Error("École non créée");
          const created: Subject[] = [];
          for (const row of subjectRows) {
            if (!row.code.trim()) continue;
            const s = await api.subjects.create({
              school_id: school.id,
              code: row.code,
              name_fr: row.name_fr || row.code,
              name_he: row.name_he || row.code,
              abbreviation: null,
              color_hex: row.color_hex || null,
              required_room_type: row.required_room_type || null,
              is_religious: false,
              is_active: true,
            });
            created.push(s);
          }
          setSubjects(created);
          return;
        }
        case "teachers": {
          if (!school.id) throw new Error("École non créée");
          const created: Teacher[] = [];
          for (const row of teacherRows) {
            if (!row.code.trim()) continue;
            const subjIds = row.qualified_subject_codes
              .split(",")
              .map((c) => c.trim())
              .filter(Boolean)
              .map((code) => subjects.find((s) => s.code === code)?.id)
              .filter((x): x is number => typeof x === "number");
            const langs = row.languages
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean);
            const t = await api.teachers.create({
              school_id: school.id,
              code: row.code,
              first_name: row.first_name || row.code,
              last_name: row.last_name || "",
              email: row.email || null,
              phone: null,
              max_hours_per_week: null,
              max_hours_per_day: null,
              languages: langs.length ? langs : ["fr"],
              is_active: true,
              qualified_subject_ids: subjIds,
            });
            created.push(t);
          }
          setTeachers(created);
          return;
        }
        case "rooms": {
          if (!school.id) throw new Error("École non créée");
          const created: Room[] = [];
          for (const row of roomRows) {
            if (!row.code.trim()) continue;
            const r = await api.rooms.create({
              school_id: school.id,
              code: row.code,
              name: row.name || row.code,
              capacity: Number(row.capacity) || 30,
              room_type: row.room_type || null,
              building: null,
              floor: null,
              equipment: null,
              is_active: true,
            });
            created.push(r);
          }
          setRooms(created);
          return;
        }
        case "groups": {
          if (!school.id) throw new Error("École non créée");
          for (const row of groupRows) {
            if (!row.label.trim() || !row.grade_id || !row.subject_code) continue;
            const subj = subjects.find((s) => s.code === row.subject_code);
            if (!subj) continue;
            const teacherIds = row.teacher_codes
              .split(",")
              .map((c) => c.trim())
              .filter(Boolean)
              .map((c) => teachers.find((t) => t.code === c)?.id)
              .filter((x): x is number => typeof x === "number");
            const classIds = row.source_class_codes
              .split(",")
              .map((c) => c.trim())
              .filter(Boolean)
              .map((c) => classes.find((cls) => cls.code === c)?.id)
              .filter((x): x is number => typeof x === "number");
            await api.groups.create({
              school_id: school.id,
              grade_id: Number(row.grade_id),
              subject_id: subj.id,
              label: row.label,
              hours_per_week: Number(row.hours_per_week) || 1,
              group_type: row.group_type,
              student_count: null,
              parallel_cohort_id: null,
              teacher_ids: teacherIds,
              source_class_ids: classIds,
            });
          }
          return;
        }
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["schools"] });
      if (step < STEPS.length - 1) {
        setStep(step + 1);
        toast.success("Étape validée ✓");
      } else {
        toast.success("École configurée ! 🎉");
        navigate("/");
      }
    },
    onError: (err: unknown) => {
      const msg = err instanceof ApiError ? err.message : String(err);
      toast.error(`Erreur : ${msg}`);
    },
  });

  const nextLabel = step === STEPS.length - 1 ? "Terminer 🎉" : "Suivant";

  function renderStep() {
    switch (STEPS[step].id) {
      case "school":
        return (
          <StepSchool
            value={school.form}
            onChange={(f) => setSchool({ ...school, form: f })}
          />
        );
      case "time-grid":
        return <StepTimeGrid slots={timeSlots} onChange={setTimeSlots} />;
      case "grades":
        return <StepGrades rows={gradeRows} onChange={setGradeRows} />;
      case "classes":
        return (
          <StepClasses rows={classRows} grades={grades} onChange={setClassRows} />
        );
      case "subjects":
        return <StepSubjects rows={subjectRows} onChange={setSubjectRows} />;
      case "teachers":
        return (
          <StepTeachers rows={teacherRows} subjects={subjects} onChange={setTeacherRows} />
        );
      case "rooms":
        return <StepRooms rows={roomRows} onChange={setRoomRows} />;
      case "groups":
        return (
          <StepGroups
            rows={groupRows}
            grades={grades}
            subjects={subjects}
            teachers={teachers}
            classes={classes}
            onChange={setGroupRows}
          />
        );
    }
  }

  return (
    <WizardLayout
      title={`Étape ${step + 1}/${STEPS.length} — ${STEPS[step].label}`}
      subtitle={
        school.form.name ? `École : ${school.form.name}` : "Configurez votre école pas à pas."
      }
      steps={STEPS}
      currentIndex={step}
      onPrev={step > 0 ? () => setStep(step - 1) : undefined}
      onNext={() => saveStep.mutate()}
      nextLabel={nextLabel}
      nextLoading={saveStep.isPending}
    >
      {renderStep()}
    </WizardLayout>
  );
}
