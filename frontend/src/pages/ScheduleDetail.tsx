/**
 * Page détail d'un planning : grille horaire avec les groupes placés.
 */

import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { TimetableGrid } from "@/components/schedule/TimetableGrid";


export default function ScheduleDetail() {
  const { id } = useParams<{ id: string }>();
  const scheduleId = Number(id);

  const { data: schedule, isLoading } = useQuery({
    queryKey: ["schedule", scheduleId],
    queryFn: () => api.schedules.get(scheduleId),
    enabled: !!scheduleId,
  });

  const schoolId = schedule?.school_id ?? null;

  const { data: groups } = useQuery({
    queryKey: ["groups", schoolId],
    queryFn: () => api.groups.list(schoolId!),
    enabled: schoolId !== null,
  });

  const { data: subjects } = useQuery({
    queryKey: ["subjects", schoolId],
    queryFn: () => api.subjects.list(schoolId!),
    enabled: schoolId !== null,
  });

  const { data: timeSlots } = useQuery({
    queryKey: ["time-grid", schoolId],
    queryFn: () => api.schools.getTimeGrid(schoolId!),
    enabled: schoolId !== null,
  });

  if (isLoading || !schedule) {
    return <p className="text-slate-500">Chargement…</p>;
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <Link
            to="/schedules"
            className="text-sm text-primary-600 hover:underline"
          >
            ← Plannings
          </Link>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
            {schedule.name}
          </h1>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant={schedule.status === "active" ? "success" : "info"}>
              {schedule.status}
            </Badge>
            {schedule.generated_at && (
              <span className="text-sm text-slate-500">
                {new Date(schedule.generated_at).toLocaleString("fr-FR")}
              </span>
            )}
          </div>
        </div>
      </header>

      <Card>
        <CardHeader>
          <h2 className="font-semibold">
            Grille horaire ({schedule.entries.length} cours)
          </h2>
        </CardHeader>
        <CardBody>
          {groups && subjects && timeSlots ? (
            <TimetableGrid
              entries={schedule.entries}
              groups={groups}
              subjects={subjects}
              timeSlots={timeSlots}
            />
          ) : (
            <p className="text-slate-500">Chargement des données…</p>
          )}
        </CardBody>
      </Card>

      {schedule.relaxed_constraints_report &&
        Object.keys(schedule.relaxed_constraints_report).length > 0 && (
          <Card>
            <CardHeader>
              <h2 className="font-semibold text-amber-700 dark:text-amber-400">
                Contraintes relaxées
              </h2>
            </CardHeader>
            <CardBody>
              <pre className="text-xs bg-slate-50 dark:bg-slate-900/50 rounded p-3 overflow-x-auto">
                {JSON.stringify(schedule.relaxed_constraints_report, null, 2)}
              </pre>
            </CardBody>
          </Card>
        )}

      <div>
        <Button variant="secondary" onClick={() => window.print()}>
          Imprimer
        </Button>
      </div>
    </div>
  );
}
