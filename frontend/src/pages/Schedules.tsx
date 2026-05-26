/**
 * Page Schedules : liste les plannings d'une école + bouton "Générer" qui
 * lance le solveur et ouvre la modal ConflictDialog en cas d'infaisabilité.
 */

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import toast from "react-hot-toast";
import { CheckCircleIcon, PlayIcon } from "@heroicons/react/24/outline";

import { api } from "@/lib/api";
import type { ConstraintConflictInfo, GenerateResponse, School } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Select } from "@/components/ui/Select";
import { ConflictDialog } from "@/components/schedule/ConflictDialog";


export default function Schedules() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();

  // Status badge avec i18n
  function StatusBadge({ status }: { status: string }) {
    const variant: "success" | "info" | "default" =
      status === "active" ? "success" : status === "draft" ? "info" : "default";
    return <Badge variant={variant}>{t(`schedules.status.${status}`)}</Badge>;
  }

  // École sélectionnée (par défaut : la première trouvée)
  const { data: schools } = useQuery({
    queryKey: ["schools"],
    queryFn: () => api.schools.list(),
  });
  const [schoolId, setSchoolId] = useState<number | null>(null);
  const currentSchoolId = schoolId ?? schools?.[0]?.id ?? null;

  // Liste des schedules
  const { data: schedules, isLoading } = useQuery({
    queryKey: ["schedules", currentSchoolId],
    queryFn: () => api.schedules.list(currentSchoolId!),
    enabled: currentSchoolId !== null,
  });

  // Conflict dialog state
  const [conflict, setConflict] = useState<{
    open: boolean;
    items: ConstraintConflictInfo[];
    solverTime: number;
  }>({ open: false, items: [], solverTime: 0 });

  // Mutation génération
  const generate = useMutation({
    mutationFn: async (params: { disabledIds?: number[] }) => {
      if (currentSchoolId === null) throw new Error("Pas d'école sélectionnée");
      return api.schedules.generate({
        school_id: currentSchoolId,
        name: t("schedules.default_name", { date: new Date().toLocaleDateString() }),
        disabled_constraint_ids: params.disabledIds ?? [],
        max_time_seconds: 30,
      });
    },
    onSuccess: (res: GenerateResponse) => {
      if (res.success) {
        toast.success(
          t("schedules.schedule_generated", {
            n: res.placed_entries,
            ms: (res.solver_time_seconds * 1000).toFixed(0),
          }),
          { duration: 4000 }
        );
        setConflict({ open: false, items: [], solverTime: 0 });
        qc.invalidateQueries({ queryKey: ["schedules"] });
        navigate(`/schedules/${res.schedule_id}`);
      } else if ("timeout" in res && res.timeout) {
        toast.error(t("conflict.timeout"));
      } else {
        setConflict({
          open: true,
          items: res.conflicts,
          solverTime: res.solver_time_seconds,
        });
      }
    },
    onError: (err: Error) => toast.error(err.message),
  });

  // Accept
  const accept = useMutation({
    mutationFn: (id: number) => api.schedules.accept(id),
    onSuccess: () => {
      toast.success(t("schedules.schedule_activated"));
      qc.invalidateQueries({ queryKey: ["schedules"] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  // Delete
  const remove = useMutation({
    mutationFn: (id: number) => api.schedules.remove(id),
    onSuccess: () => {
      toast.success(t("schedules.deleted"));
      qc.invalidateQueries({ queryKey: ["schedules"] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  if (!schools || schools.length === 0) {
    return (
      <Card>
        <CardBody>
          <p className="text-slate-600 dark:text-slate-400">
            {t("schedules.no_school_yet")}{" "}
            <Link to="/wizard" className="text-primary-600 underline">
              {t("schedules.wizard_link")}
            </Link>
            .
          </p>
        </CardBody>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {t("schedules.title")}
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {t("schedules.subtitle")}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select
            value={currentSchoolId ?? ""}
            onChange={(e) => setSchoolId(Number(e.target.value))}
            options={(schools ?? []).map((s: School) => ({
              value: s.id,
              label: s.name,
            }))}
          />
          <Button
            onClick={() => generate.mutate({})}
            loading={generate.isPending}
            disabled={currentSchoolId === null}
          >
            <PlayIcon className="h-4 w-4" />
            {t("actions.generate")}
          </Button>
        </div>
      </header>

      <Card>
        <CardHeader>
          <h2 className="font-semibold">{t("schedules.existing")}</h2>
        </CardHeader>
        <CardBody>
          {isLoading && <p className="text-sm text-slate-500">{t("actions.loading")}</p>}
          {!isLoading && (!schedules || schedules.length === 0) && (
            <p className="text-sm text-slate-500">{t("schedules.no_schedules")}</p>
          )}
          {schedules && schedules.length > 0 && (
            <ul className="divide-y divide-slate-200 dark:divide-slate-700">
              {schedules.map((s) => (
                <li key={s.id} className="py-3 flex items-center justify-between gap-3 flex-wrap">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => navigate(`/schedules/${s.id}`)}
                      className="text-left hover:underline"
                    >
                      <div className="font-medium text-slate-900 dark:text-slate-100">
                        {s.name}
                      </div>
                      <div className="text-xs text-slate-500">
                        {s.generated_at
                          ? new Date(s.generated_at).toLocaleString()
                          : "—"}
                      </div>
                    </button>
                    <StatusBadge status={s.status} />
                  </div>
                  <div className="flex items-center gap-2">
                    {s.status === "draft" && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => accept.mutate(s.id)}
                        loading={accept.isPending && accept.variables === s.id}
                      >
                        <CheckCircleIcon className="h-4 w-4" />
                        {t("actions.activate")}
                      </Button>
                    )}
                    {s.status !== "active" && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          if (confirm(t("schedules.delete_confirm", { name: s.name }))) {
                            remove.mutate(s.id);
                          }
                        }}
                      >
                        {t("schedules.delete")}
                      </Button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      <ConflictDialog
        open={conflict.open}
        conflicts={conflict.items}
        solverTimeSeconds={conflict.solverTime}
        onClose={() => setConflict({ ...conflict, open: false })}
        onRetry={(disabledIds) => generate.mutate({ disabledIds })}
        retrying={generate.isPending}
      />
    </div>
  );
}
