/**
 * Page "מדיניות בית הספר" / Politiques école.
 *
 * Templates "1 clic" pour créer les contraintes globales communes :
 * - Prière matin obligatoire (créneau 0 tous les jours)
 * - Yom Kippour / Shabbat (jour entier bloqué)
 * - Pause déjeuner (créneau X)
 * - Vendredi court (créneaux après X bloqués)
 *
 * Évite à l'admin d'ouvrir le form générique /constraints à chaque fois.
 */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import toast from "react-hot-toast";
import {
  SunIcon,
  MoonIcon,
  CakeIcon,
  CalendarIcon,
  AcademicCapIcon,
  CheckCircleIcon,
} from "@heroicons/react/24/outline";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Modal, ModalBody, ModalFooter } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { useCurrentSchool } from "@/components/layout/SchoolContext";


interface Template {
  id: string;
  icon: typeof SunIcon;
  title_he: string;
  title_fr: string;
  desc_he: string;
  desc_fr: string;
  // Si requiresInput est true, la modal demande des params
  requiresInput?: "date" | "slot" | "from_slot";
  // Action : retourne le body de POST /constraints
  build: (school_id: number, input?: any) => any;
}


const TEMPLATES: Template[] = [
  {
    id: "morning-prayer",
    icon: SunIcon,
    title_he: "תפילת בוקר חובה (משבצת 0 כל יום)",
    title_fr: "Prière du matin obligatoire (créneau 0 tous jours)",
    desc_he: "חוסם את משבצת 0 לכל ימי השבוע — מיועד לתפילה.",
    desc_fr: "Bloque le créneau 0 sur tous les jours d'école — réservé prière.",
    build: (school_id) => ({
      school_id,
      constraint_type: "block_slot_school",
      priority: "hard",
      weight: null,
      parameters: { days: [0, 1, 2, 3, 4], slot_indices: [0] },
      is_active: true,
      origin_role: "school_admin",
      origin_user_id: null,
      origin_description: "תפילת בוקר",
      origin_raw_text: null,
    }),
  },
  {
    id: "friday-short",
    icon: MoonIcon,
    title_he: "יום שישי קצר (סוף ב-משבצת 4)",
    title_fr: "Vendredi court (fin créneau 4)",
    desc_he: "ביום שישי, רק 4 שיעורים. שאר המשבצות חסומות.",
    desc_fr: "Vendredi : seulement les 4 premiers créneaux. Le reste est bloqué.",
    build: (school_id) => ({
      school_id,
      constraint_type: "block_slot_school",
      priority: "hard",
      weight: null,
      parameters: { days: [5], slot_indices: [4, 5, 6, 7, 8, 9, 10] },
      is_active: true,
      origin_role: "school_admin",
      origin_user_id: null,
      origin_description: "יום שישי קצר",
      origin_raw_text: null,
    }),
  },
  {
    id: "lunch-break",
    icon: CakeIcon,
    title_he: "הפסקת צהריים (משבצת 5)",
    title_fr: "Pause déjeuner (créneau 5)",
    desc_he: "חוסם את משבצת 5 בכל ימי השבוע — להפסקת אוכל.",
    desc_fr: "Bloque le créneau 5 tous les jours pour la pause déjeuner.",
    requiresInput: "slot",
    build: (school_id, slot: number) => ({
      school_id,
      constraint_type: "block_slot_school",
      priority: "hard",
      weight: null,
      parameters: { days: [0, 1, 2, 3, 4], slot_indices: [slot] },
      is_active: true,
      origin_role: "school_admin",
      origin_user_id: null,
      origin_description: `הפסקת צהריים (משבצת ${slot + 1})`,
      origin_raw_text: null,
    }),
  },
  {
    id: "holiday-closure",
    icon: CalendarIcon,
    title_he: "חג / יום סגור",
    title_fr: "Jour férié / fermeture",
    desc_he: "סגירה מלאה ביום מסוים (יום כיפור, חגים…).",
    desc_fr: "Fermeture complète sur un jour donné (Yom Kippour, fêtes…).",
    requiresInput: "date",
    build: (school_id, day: number) => ({
      school_id,
      constraint_type: "block_slot_school",
      priority: "hard",
      weight: null,
      parameters: {
        days: [day],
        slot_indices: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
      },
      is_active: true,
      origin_role: "school_admin",
      origin_user_id: null,
      origin_description: `חג — סגירה`,
      origin_raw_text: null,
    }),
  },
  {
    id: "religious-morning-only",
    icon: AcademicCapIcon,
    title_he: "מקצועות דת בבוקר בלבד",
    title_fr: "Matières religieuses en matinée uniquement",
    desc_he: "מקצועות דת (תנ\"ך, תלמוד) חייבים להיות במשבצות 1-4.",
    desc_fr: "Matières religieuses doivent être placées créneaux 1-4.",
    build: (_school_id) => ({
      // Note : ce template nécessiterait subject_id, on le laisse en placeholder
      // pour future implémentation (filter par is_religious)
      _placeholder: true,
    }),
  },
];


const DAY_LABELS_HE = ["א'", "ב'", "ג'", "ד'", "ה'", "ו'", "ש'"];
const DAY_LABELS_FR = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];


export default function Policies() {
  const { t, i18n } = useTranslation();
  const isHe = i18n.language === "he";
  const qc = useQueryClient();
  const { currentId: schoolId } = useCurrentSchool();

  const { data: constraints } = useQuery({
    queryKey: ["constraints", schoolId],
    queryFn: () => api.constraints.list(schoolId!),
    enabled: schoolId !== null,
  });

  const [pendingTpl, setPendingTpl] = useState<Template | null>(null);
  const [inputDay, setInputDay] = useState<number>(4);
  const [inputSlot, setInputSlot] = useState<number>(5);

  const applyTemplate = useMutation({
    mutationFn: async (body: any) => api.constraints.create(body),
    onSuccess: () => {
      toast.success("✓");
      qc.invalidateQueries({ queryKey: ["constraints", schoolId] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  function handleApply(tpl: Template) {
    if (!schoolId) return;
    if (tpl.id === "religious-morning-only") {
      toast.error(isHe ? "פיצ׳ר זה דורש פיתוח נוסף" : "Feature à compléter");
      return;
    }
    if (tpl.requiresInput) {
      setPendingTpl(tpl);
      return;
    }
    applyTemplate.mutate(tpl.build(schoolId));
  }

  function confirmApply() {
    if (!pendingTpl || !schoolId) return;
    const input = pendingTpl.requiresInput === "date" ? inputDay : inputSlot;
    applyTemplate.mutate(pendingTpl.build(schoolId, input));
    setPendingTpl(null);
  }

  // Compter combien de contraintes "school" sont actives
  const schoolPoliciesActive = (constraints ?? []).filter(
    (c) => c.constraint_type === "block_slot_school" && c.is_active
  );

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">
          📋 {isHe ? "מדיניות בית הספר" : "Politiques école"}
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
          {isHe
            ? "תבניות מהירות לחוקי בית הספר. לחץ ״החל״ כדי להוסיף את האילוץ."
            : "Templates rapides pour les règles globales. Cliquez « Appliquer » pour ajouter la contrainte."}
        </p>
        <p className="text-xs text-slate-500 mt-2">
          {isHe
            ? `${schoolPoliciesActive.length} מדיניות פעילות (block_slot_school)`
            : `${schoolPoliciesActive.length} politiques actives (block_slot_school)`}
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {TEMPLATES.map((tpl) => {
          const Icon = tpl.icon;
          return (
            <Card key={tpl.id}>
              <CardBody>
                <div className="flex items-start gap-3">
                  <div className="rounded-lg bg-primary-100 dark:bg-primary-900/40 p-2">
                    <Icon className="h-6 w-6 text-primary-700 dark:text-primary-300" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                      {isHe ? tpl.title_he : tpl.title_fr}
                    </h3>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                      {isHe ? tpl.desc_he : tpl.desc_fr}
                    </p>
                    <div className="mt-3">
                      <Button
                        size="sm"
                        onClick={() => handleApply(tpl)}
                        loading={applyTemplate.isPending}
                      >
                        <CheckCircleIcon className="h-4 w-4" />
                        {isHe ? "החל" : "Appliquer"}
                      </Button>
                    </div>
                  </div>
                </div>
              </CardBody>
            </Card>
          );
        })}
      </div>

      {/* Liste des politiques actives */}
      {schoolPoliciesActive.length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="font-semibold">
              {isHe ? "מדיניות פעילות" : "Politiques actives"} ({schoolPoliciesActive.length})
            </h2>
          </CardHeader>
          <CardBody>
            <ul className="divide-y divide-slate-200 dark:divide-slate-700">
              {schoolPoliciesActive.map((c) => {
                const p = c.parameters as any;
                const days = (p.days ?? []) as number[];
                const slots = (p.slot_indices ?? []) as number[];
                const dayLabels = isHe ? DAY_LABELS_HE : DAY_LABELS_FR;
                return (
                  <li key={c.id} className="py-2 flex items-center justify-between">
                    <div>
                      <div className="font-medium">
                        {c.origin_description ?? c.constraint_type}
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5 flex gap-2 flex-wrap">
                        <Badge variant="default">
                          {days.map((d) => dayLabels[d]).join(", ")}
                        </Badge>
                        <Badge variant="default">
                          {isHe ? "משבצות" : "Créneaux"} {slots.map((s) => s + 1).join(", ")}
                        </Badge>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={async () => {
                        await api.constraints.remove(c.id);
                        qc.invalidateQueries({ queryKey: ["constraints", schoolId] });
                        toast.success(t("schedules.deleted"));
                      }}
                    >
                      🗑
                    </Button>
                  </li>
                );
              })}
            </ul>
          </CardBody>
        </Card>
      )}

      {/* Modal pour les templates qui demandent un input */}
      <Modal
        open={pendingTpl !== null}
        onClose={() => setPendingTpl(null)}
        title={pendingTpl ? (isHe ? pendingTpl.title_he : pendingTpl.title_fr) : ""}
      >
        <ModalBody>
          {pendingTpl?.requiresInput === "date" && (
            <div className="space-y-3">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                {isHe ? "באיזה יום בשבוע ?" : "Quel jour de la semaine ?"}
              </p>
              <div className="flex gap-2 flex-wrap">
                {(isHe ? DAY_LABELS_HE : DAY_LABELS_FR).slice(0, 6).map((d, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setInputDay(i)}
                    className={`min-h-[44px] min-w-[44px] rounded-lg border text-sm font-medium ${
                      inputDay === i
                        ? "bg-primary-600 text-white border-primary-600"
                        : "bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-600"
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>
          )}
          {pendingTpl?.requiresInput === "slot" && (
            <div className="space-y-3">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                {isHe ? "איזו משבצת ?" : "Quel créneau ?"}
              </p>
              <Input
                type="number"
                min={1}
                max={11}
                value={inputSlot + 1}
                onChange={(e) => setInputSlot(Number(e.target.value) - 1)}
              />
            </div>
          )}
        </ModalBody>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setPendingTpl(null)}>
            {t("actions.cancel")}
          </Button>
          <Button onClick={confirmApply} loading={applyTemplate.isPending}>
            {isHe ? "החל" : "Appliquer"}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
