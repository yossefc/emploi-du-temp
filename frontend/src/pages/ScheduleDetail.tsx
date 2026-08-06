/**
 * Page détail d'un planning : grille horaire filtrable par classe ou par prof.
 */

import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { api } from "@/lib/api";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { TimetableGrid } from "@/components/schedule/TimetableGrid";

type ViewMode = "class" | "teacher" | "all";


export default function ScheduleDetail() {
  const { t, i18n } = useTranslation();
  const isHe = i18n.language === "he";
  const { id } = useParams<{ id: string }>();
  const scheduleId = Number(id);

  const [mode, setMode] = useState<ViewMode>("class");
  const [classId, setClassId] = useState<number | null>(null);
  const [teacherId, setTeacherId] = useState<number | null>(null);

  const { data: schedule, isLoading } = useQuery({
    queryKey: ["schedule", scheduleId],
    queryFn: () => api.schedules.get(scheduleId),
    enabled: !!scheduleId,
  });

  const schoolId = schedule?.school_id ?? null;
  const on = { enabled: schoolId !== null };

  const { data: groups } = useQuery({
    queryKey: ["groups", schoolId], queryFn: () => api.groups.list(schoolId!), ...on });
  const { data: subjects } = useQuery({
    queryKey: ["subjects", schoolId], queryFn: () => api.subjects.list(schoolId!), ...on });
  const { data: timeSlots } = useQuery({
    queryKey: ["time-grid", schoolId], queryFn: () => api.schools.getTimeGrid(schoolId!), ...on });
  const { data: classes } = useQuery({
    queryKey: ["classes", schoolId], queryFn: () => api.classes.list(schoolId!), ...on });
  const { data: teachers } = useQuery({
    queryKey: ["teachers", schoolId], queryFn: () => api.teachers.list(schoolId!), ...on });

  // Sélectionner la première classe dès qu'elles sont chargées
  useEffect(() => {
    if (classId === null && classes && classes.length > 0) setClassId(classes[0].id);
  }, [classes, classId]);
  useEffect(() => {
    if (teacherId === null && teachers && teachers.length > 0) setTeacherId(teachers[0].id);
  }, [teachers, teacherId]);

  if (isLoading || !schedule) {
    return <p className="text-slate-500">{t("actions.loading")}</p>;
  }

  const ready = groups && subjects && timeSlots;
  const activeClass = mode === "class" ? classId : null;
  const activeTeacher = mode === "teacher" ? teacherId : null;

  // Nombre de cours affichés dans la vue courante
  const shownCount = !groups
    ? 0
    : schedule.entries.filter((e) => {
        const g = groups.find((x) => x.id === e.group_id);
        if (!g) return false;
        if (activeClass != null) return g.source_class_ids.includes(activeClass);
        if (activeTeacher != null) return g.teacher_ids.includes(activeTeacher);
        return true;
      }).length;

  const TABS: { key: ViewMode; label: string }[] = [
    { key: "class", label: isHe ? "לפי כיתה" : "Par classe" },
    { key: "teacher", label: isHe ? "לפי מורה" : "Par prof" },
    { key: "all", label: isHe ? "הכל" : "Tout" },
  ];

  return (
    <div className="space-y-6">
      <header className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <Link to="/schedules" className="text-sm text-primary-600 hover:underline">
            {t("schedules.back_to_list")}
          </Link>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
            {schedule.name}
          </h1>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <Badge variant={schedule.status === "active" ? "success" : "info"}>
              {t(`schedules.status.${schedule.status}`)}
            </Badge>
            <span className="text-sm text-slate-500">
              {schedule.entries.length} {isHe ? "שיעורים" : "cours"}
            </span>
            {schedule.generated_at && (
              <span className="text-sm text-slate-500">
                · {new Date(schedule.generated_at).toLocaleString()}
              </span>
            )}
          </div>
        </div>
        <Button variant="secondary" onClick={() => window.print()}>
          {t("actions.print")}
        </Button>
      </header>

      <Card>
        <CardHeader className="flex flex-wrap items-center gap-3">
          {/* Onglets de mode */}
          <div className="inline-flex rounded-lg border border-slate-300 dark:border-slate-600 overflow-hidden">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setMode(tab.key)}
                className={
                  "px-3 py-2 text-sm font-medium transition-colors " +
                  (mode === tab.key
                    ? "bg-primary-600 text-white"
                    : "bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700")
                }
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Sélecteur contextuel */}
          {mode === "class" && classes && (
            <div className="min-w-[200px]">
              <Select
                value={classId ?? ""}
                onChange={(e) => setClassId(Number(e.target.value))}
                options={classes.map((c) => ({ value: c.id, label: c.code }))}
              />
            </div>
          )}
          {mode === "teacher" && teachers && (
            <div className="min-w-[260px]">
              <Select
                value={teacherId ?? ""}
                onChange={(e) => setTeacherId(Number(e.target.value))}
                options={teachers.map((tt) => ({
                  value: tt.id,
                  label: `${tt.first_name} ${tt.last_name}`.trim(),
                }))}
              />
            </div>
          )}

          <span className="text-sm text-slate-500">
            {shownCount} {isHe ? "שיעורים בתצוגה" : "cours affichés"}
          </span>
        </CardHeader>
        <CardBody>
          {ready ? (
            <TimetableGrid
              entries={schedule.entries}
              groups={groups}
              subjects={subjects}
              timeSlots={timeSlots}
              teachers={teachers}
              filterClassId={activeClass}
              filterTeacherId={activeTeacher}
            />
          ) : (
            <p className="text-slate-500">{t("actions.loading")}</p>
          )}
        </CardBody>
      </Card>

      {/* Légende des couleurs */}
      {subjects && subjects.length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="font-semibold text-sm">
              {isHe ? "מקרא צבעים" : "Légende des couleurs"}
            </h2>
          </CardHeader>
          <CardBody>
            <div className="flex flex-wrap gap-2">
              {subjects.map((s) => (
                <span
                  key={s.id}
                  className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 dark:border-slate-700 px-2.5 py-1 text-xs"
                >
                  <span
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: s.color_hex ?? "#94a3b8" }}
                  />
                  {s.name_he}
                </span>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {schedule.relaxed_constraints_report &&
        Object.keys(schedule.relaxed_constraints_report).length > 0 && (
          <Card>
            <CardHeader>
              <h2 className="font-semibold text-amber-700 dark:text-amber-400">
                {t("schedules.relaxed_report")}
              </h2>
            </CardHeader>
            <CardBody>
              <pre className="text-xs bg-slate-50 dark:bg-slate-900/50 rounded p-3 overflow-x-auto">
                {JSON.stringify(schedule.relaxed_constraints_report, null, 2)}
              </pre>
            </CardBody>
          </Card>
        )}
    </div>
  );
}
