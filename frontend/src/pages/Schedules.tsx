/**
 * Page Schedules : liste les plannings d'une école + bouton "Générer" qui
 * lance le solveur et ouvre la modal ConflictDialog en cas d'infaisabilité.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { CheckCircleIcon, ClockIcon, ArchiveBoxIcon, PlayIcon } from "@heroicons/react/24/outline";

import { api } from "@/lib/api";
import type { ConstraintConflictInfo, GenerateResponse, School } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Select } from "@/components/ui/Select";
import { ConflictDialog } from "@/components/schedule/ConflictDialog";


function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case "active":
      return <Badge variant="success">Actif</Badge>;
    case "draft":
      return <Badge variant="info">Brouillon</Badge>;
    case "archived":
      return <Badge variant="default">Archivé</Badge>;
    default:
      return <Badge>{status}</Badge>;
  }
}


export default function Schedules() {
  const navigate = useNavigate();
  const qc = useQueryClient();

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
    mutationFn: async (params: { disabledIds?: number[]; name?: string }) => {
      if (currentSchoolId === null) throw new Error("Pas d'école sélectionnée");
      return api.schedules.generate({
        school_id: currentSchoolId,
        name: params.name ?? `Planning ${new Date().toLocaleDateString("fr-FR")}`,
        disabled_constraint_ids: params.disabledIds ?? [],
        max_time_seconds: 30,
      });
    },
    onSuccess: (res: GenerateResponse) => {
      if (res.success) {
        toast.success(
          `Planning généré : ${res.placed_entries} cours placés en ${(res.solver_time_seconds * 1000).toFixed(0)} ms`,
          { duration: 4000 }
        );
        setConflict({ open: false, items: [], solverTime: 0 });
        qc.invalidateQueries({ queryKey: ["schedules"] });
        navigate(`/schedules/${res.schedule_id}`);
      } else if ("timeout" in res && res.timeout) {
        toast.error("Timeout solveur — essayez d'augmenter max_time_seconds");
      } else {
        setConflict({
          open: true,
          items: res.conflicts,
          solverTime: res.solver_time_seconds,
        });
      }
    },
    onError: (err: Error) => {
      toast.error(`Erreur : ${err.message}`);
    },
  });

  // Accept
  const accept = useMutation({
    mutationFn: (id: number) => api.schedules.accept(id),
    onSuccess: () => {
      toast.success("Planning activé ✓");
      qc.invalidateQueries({ queryKey: ["schedules"] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  // Delete
  const remove = useMutation({
    mutationFn: (id: number) => api.schedules.remove(id),
    onSuccess: () => {
      toast.success("Supprimé");
      qc.invalidateQueries({ queryKey: ["schedules"] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  if (!schools || schools.length === 0) {
    return (
      <Card>
        <CardBody>
          <p className="text-slate-600 dark:text-slate-400">
            Aucune école. Commencez par le{" "}
            <a href="/wizard" className="text-primary-600 underline">
              wizard de configuration
            </a>
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
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Plannings</h1>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Générez des emplois du temps et résolvez les conflits.
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
            Générer
          </Button>
        </div>
      </header>

      <Card>
        <CardHeader>
          <h2 className="font-semibold">Plannings existants</h2>
        </CardHeader>
        <CardBody>
          {isLoading && (
            <p className="text-sm text-slate-500">Chargement…</p>
          )}
          {!isLoading && (!schedules || schedules.length === 0) && (
            <p className="text-sm text-slate-500">
              Aucun planning. Cliquez sur "Générer" pour en créer un.
            </p>
          )}
          {schedules && schedules.length > 0 && (
            <ul className="divide-y divide-slate-200 dark:divide-slate-700">
              {schedules.map((s) => (
                <li
                  key={s.id}
                  className="py-3 flex items-center justify-between gap-3 flex-wrap"
                >
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
                          ? new Date(s.generated_at).toLocaleString("fr-FR")
                          : "Non généré"}
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
                        Activer
                      </Button>
                    )}
                    {s.status !== "active" && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          if (confirm(`Supprimer "${s.name}" ?`)) remove.mutate(s.id);
                        }}
                      >
                        Supprimer
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

// Marker utilisé pour le filtrage des icônes dans l'arbre (évite warning import inutile)
void [ArchiveBoxIcon, ClockIcon];
