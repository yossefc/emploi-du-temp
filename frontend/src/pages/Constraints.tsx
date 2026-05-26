/**
 * Page Constraints : créer/lister/activer/désactiver les aliutsim (contraintes).
 *
 * Pour MVP on supporte les 5 types les plus utiles via un formulaire dédié.
 * Les autres types sont disponibles en mode "JSON brut" pour l'admin avancé.
 */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import toast from "react-hot-toast";
import { PlusIcon, EyeIcon, EyeSlashIcon } from "@heroicons/react/24/outline";

import { api } from "@/lib/api";
import type { Constraint } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Modal, ModalBody, ModalFooter } from "@/components/ui/Modal";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { DataList } from "@/components/ui/DataList";
import { useCurrentSchool } from "@/components/layout/SchoolContext";


type ConstraintType =
  | "block_slot_teacher"
  | "block_slot_class"
  | "block_slot_room"
  | "group_hours_per_week"
  | "teacher_max_hours_week"
  | "other";


const DAY_LABELS_HE = ["א", "ב", "ג", "ד", "ה", "ו", "ש"];
const DAY_LABELS_FR = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];


export default function Constraints() {
  const { t, i18n } = useTranslation();
  const isHe = i18n.language === "he";
  const dayLabels = isHe ? DAY_LABELS_HE : DAY_LABELS_FR;
  const qc = useQueryClient();
  const { currentId: schoolId } = useCurrentSchool();

  const { data: constraints, isLoading } = useQuery({
    queryKey: ["constraints", schoolId],
    queryFn: () => api.constraints.list(schoolId!),
    enabled: schoolId !== null,
  });
  const { data: teachers } = useQuery({
    queryKey: ["teachers", schoolId],
    queryFn: () => api.teachers.list(schoolId!),
    enabled: schoolId !== null,
  });
  const { data: classes } = useQuery({
    queryKey: ["classes", schoolId],
    queryFn: () => api.classes.list(schoolId!),
    enabled: schoolId !== null,
  });
  const { data: rooms } = useQuery({
    queryKey: ["rooms", schoolId],
    queryFn: () => api.rooms.list(schoolId!),
    enabled: schoolId !== null,
  });
  const { data: groups } = useQuery({
    queryKey: ["groups", schoolId],
    queryFn: () => api.groups.list(schoolId!),
    enabled: schoolId !== null,
  });

  // Form state
  const [modalOpen, setModalOpen] = useState(false);
  const [ctype, setCtype] = useState<ConstraintType>("block_slot_teacher");
  const [origin_description, setOriginDescription] = useState("");

  // Type-specific form state
  const [blockTarget, setBlockTarget] = useState<number | "">("");
  const [blockDays, setBlockDays] = useState<Set<number>>(new Set([1]));
  const [blockSlots, setBlockSlots] = useState<Set<number>>(new Set([0]));
  const [maxHours, setMaxHours] = useState(24);
  const [hours, setHours] = useState(2);
  const [groupId, setGroupId] = useState<number | "">("");

  const create = useMutation({
    mutationFn: async () => {
      if (!schoolId) throw new Error("No school");

      let parameters: Record<string, unknown> = {};
      let origin_role: "teacher" | "school_admin" = "school_admin";

      if (ctype.startsWith("block_slot_")) {
        if (!blockTarget) throw new Error("Cible requise");
        parameters = {
          days: Array.from(blockDays),
          slot_indices: Array.from(blockSlots),
          target_id: blockTarget,
        };
        if (ctype === "block_slot_teacher") origin_role = "teacher";
      } else if (ctype === "group_hours_per_week") {
        if (!groupId) throw new Error("Group requis");
        parameters = { group_id: Number(groupId), hours };
      } else if (ctype === "teacher_max_hours_week") {
        if (!blockTarget) throw new Error("Prof requis");
        parameters = { teacher_id: blockTarget, max_hours: maxHours };
      }

      return api.constraints.create({
        school_id: schoolId,
        constraint_type: ctype as any,
        priority: "hard" as any,
        weight: null,
        parameters,
        is_active: true,
        origin_role: origin_role as any,
        origin_user_id: null,
        origin_description: origin_description || null,
        origin_raw_text: null,
      });
    },
    onSuccess: () => {
      toast.success("✓");
      qc.invalidateQueries({ queryKey: ["constraints", schoolId] });
      setModalOpen(false);
      setBlockTarget(""); setBlockDays(new Set([1])); setBlockSlots(new Set([0]));
      setMaxHours(24); setHours(2); setGroupId("");
      setOriginDescription("");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const toggleActive = useMutation({
    mutationFn: (c: Constraint) => api.constraints.update(c.id, { is_active: !c.is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["constraints", schoolId] }),
    onError: (e: Error) => toast.error(e.message),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.constraints.remove(id),
    onSuccess: () => {
      toast.success(t("schedules.deleted"));
      qc.invalidateQueries({ queryKey: ["constraints", schoolId] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  function describe(c: Constraint): string {
    const p = c.parameters as any;
    if (c.constraint_type === "block_slot_teacher") {
      const t = teachers?.find((x) => x.id === p.target_id);
      const nDays = (p.days ?? []).length;
      const nSlots = (p.slot_indices ?? []).length;
      return `${(t ? `${t.first_name} ${t.last_name}` : `#${p.target_id}`)} — ${nDays}j × ${nSlots}créneaux`;
    }
    if (c.constraint_type === "block_slot_class") {
      const cl = classes?.find((x) => x.id === p.target_id);
      return `Classe ${cl?.code ?? `#${p.target_id}`} — ${(p.days ?? []).length}j × ${(p.slot_indices ?? []).length}cr`;
    }
    if (c.constraint_type === "block_slot_room") {
      const r = rooms?.find((x) => x.id === p.target_id);
      return `Salle ${r?.code ?? `#${p.target_id}`} — ${(p.days ?? []).length}j × ${(p.slot_indices ?? []).length}cr`;
    }
    if (c.constraint_type === "group_hours_per_week") {
      const g = groups?.find((x) => x.id === p.group_id);
      return `${g?.label ?? `#${p.group_id}`} = ${p.hours}h/sem`;
    }
    if (c.constraint_type === "teacher_max_hours_week") {
      const t = teachers?.find((x) => x.id === p.teacher_id);
      return `${t ? `${t.first_name} ${t.last_name}` : `#${p.teacher_id}`} ≤ ${p.max_hours}h/sem`;
    }
    return JSON.stringify(p);
  }

  function toggleDay(d: number) {
    const s = new Set(blockDays);
    if (s.has(d)) s.delete(d); else s.add(d);
    setBlockDays(s);
  }
  function toggleSlot(s: number) {
    const set = new Set(blockSlots);
    if (set.has(s)) set.delete(s); else set.add(s);
    setBlockSlots(set);
  }

  // Construct target options selon le type
  function targetOptions() {
    if (ctype === "block_slot_teacher" || ctype === "teacher_max_hours_week") {
      return (teachers ?? []).map((t) => ({ value: t.id, label: `${t.code} — ${t.first_name} ${t.last_name}` }));
    }
    if (ctype === "block_slot_class") {
      return (classes ?? []).map((c) => ({ value: c.id, label: c.code }));
    }
    if (ctype === "block_slot_room") {
      return (rooms ?? []).map((r) => ({ value: r.id, label: r.code }));
    }
    return [];
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold">{t("nav.constraints")}</h1>
        <Button onClick={() => setModalOpen(true)}>
          <PlusIcon className="h-4 w-4" />
          {t("actions.create")}
        </Button>
      </header>

      <Card>
        <CardHeader>
          <h2 className="font-semibold">
            {constraints?.length ?? 0} {t("nav.constraints")}
          </h2>
        </CardHeader>
        <CardBody>
          <DataList<Constraint>
            data={constraints}
            loading={isLoading}
            onDelete={(row) => remove.mutate(row.id)}
            deletingId={remove.isPending ? (remove.variables as number) : null}
            columns={[
              {
                key: "is_active",
                label: "",
                width: "60px",
                render: (r) => (
                  <button
                    type="button"
                    onClick={() => toggleActive.mutate(r)}
                    className={`text-${r.is_active ? "primary" : "slate"}-500 hover:opacity-70`}
                    title={r.is_active ? "Active" : "Désactivée"}
                  >
                    {r.is_active ? <EyeIcon className="h-5 w-5" /> : <EyeSlashIcon className="h-5 w-5 text-slate-400" />}
                  </button>
                ),
              },
              {
                key: "constraint_type",
                label: t("columns.type"),
                width: "20%",
                render: (r) => <Badge variant="default">{t(`constraint_type.${r.constraint_type}`, r.constraint_type)}</Badge>,
              },
              {
                key: "params",
                label: t("columns.detail"),
                render: (r) => <span className="text-sm">{describe(r)}</span>,
              },
              {
                key: "origin",
                label: t("columns.origin"),
                render: (r) => <span className="text-xs text-slate-500">{r.origin_description ?? r.origin_role}</span>,
              },
            ]}
          />
        </CardBody>
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={t("actions.create")} size="lg">
        <ModalBody>
          <div className="space-y-4">
            <Select
              label="Type d'aliuts / סוג אילוץ"
              value={ctype}
              onChange={(e) => setCtype(e.target.value as ConstraintType)}
              options={[
                { value: "block_slot_teacher", label: "אי-זמינות מורה / Indispo prof" },
                { value: "block_slot_class", label: "אי-זמינות כיתה / Indispo classe" },
                { value: "block_slot_room", label: "חדר לא זמין / Salle indispo" },
                { value: "group_hours_per_week", label: "נפח שעות קבוצה / Volume groupe" },
                { value: "teacher_max_hours_week", label: "תקרה שבועית למורה / Plafond prof/sem" },
              ]}
            />

            {/* Form spécifique par type */}
            {(ctype === "block_slot_teacher" || ctype === "block_slot_class" || ctype === "block_slot_room") && (
              <>
                <Select
                  label="Cible / יעד *"
                  value={blockTarget}
                  onChange={(e) => setBlockTarget(e.target.value ? Number(e.target.value) : "")}
                  options={[{ value: "", label: "—" }, ...targetOptions()]}
                />

                <div>
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300 block mb-1">
                    Jours / ימים
                  </label>
                  <div className="flex gap-2 flex-wrap">
                    {dayLabels.map((d, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => toggleDay(i)}
                        className={`min-h-[44px] min-w-[44px] rounded-lg border text-sm font-medium ${
                          blockDays.has(i)
                            ? "bg-primary-600 text-white border-primary-600"
                            : "bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-600"
                        }`}
                      >
                        {d}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300 block mb-1">
                    Créneaux / משבצות (0-7)
                  </label>
                  <div className="flex gap-2 flex-wrap">
                    {Array.from({ length: 8 }, (_, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => toggleSlot(i)}
                        className={`min-h-[44px] min-w-[44px] rounded-lg border text-sm font-medium ${
                          blockSlots.has(i)
                            ? "bg-primary-600 text-white border-primary-600"
                            : "bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-600"
                        }`}
                      >
                        {i + 1}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {ctype === "group_hours_per_week" && (
              <>
                <Select
                  label="Groupe *"
                  value={groupId}
                  onChange={(e) => setGroupId(e.target.value ? Number(e.target.value) : "")}
                  options={[
                    { value: "", label: "—" },
                    ...(groups ?? []).map((g) => ({ value: g.id, label: g.label })),
                  ]}
                />
                <div>
                  <label className="text-sm font-medium block mb-1">Heures / שעות</label>
                  <input
                    type="number" min={1} max={40}
                    value={hours}
                    onChange={(e) => setHours(Number(e.target.value))}
                    className="rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2"
                  />
                </div>
              </>
            )}

            {ctype === "teacher_max_hours_week" && (
              <>
                <Select
                  label="Prof *"
                  value={blockTarget}
                  onChange={(e) => setBlockTarget(e.target.value ? Number(e.target.value) : "")}
                  options={[{ value: "", label: "—" }, ...targetOptions()]}
                />
                <div>
                  <label className="text-sm font-medium block mb-1">Plafond / תקרה (h/sem)</label>
                  <input
                    type="number" min={1} max={50}
                    value={maxHours}
                    onChange={(e) => setMaxHours(Number(e.target.value))}
                    className="rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2"
                  />
                </div>
              </>
            )}

            <div>
              <label className="text-sm font-medium block mb-1">Description / תיאור (optionnel)</label>
              <input
                type="text"
                value={origin_description}
                onChange={(e) => setOriginDescription(e.target.value)}
                placeholder="Sarah indispo le lundi matin"
                className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2"
              />
            </div>
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setModalOpen(false)}>
            {t("actions.cancel")}
          </Button>
          <Button onClick={() => create.mutate()} loading={create.isPending}>
            {t("actions.create")}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
