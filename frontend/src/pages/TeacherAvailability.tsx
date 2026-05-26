/**
 * Page "Disponibilité prof" / "זמינות מורה".
 *
 * Consolide en une seule page :
 * - Grille jour × créneau cliquable (toggle disponible/indispo)
 * - Plafonds horaires (sem, jour, consécutifs)
 * - Co-enseignants (binômes "doivent enseigner ensemble")
 *
 * Au save :
 * - Supprime toutes les contraintes block_slot_teacher / teacher_max_*
 *   teachers_must_teach_together où ce prof est target/partie prenante
 * - Recrée une contrainte consolidée par type avec les params actuels
 *
 * Approche pragmatique : 1 contrainte block_slot_teacher unique par prof.
 * Si le prof avait plusieurs contraintes indépendantes, elles sont fusionnées.
 */

import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import toast from "react-hot-toast";
import { ArrowLeftIcon } from "@heroicons/react/24/outline";

import { api } from "@/lib/api";
import type { Constraint } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { MultiSelect } from "@/components/ui/MultiSelect";
import { Badge } from "@/components/ui/Badge";
import { useCurrentSchool } from "@/components/layout/SchoolContext";


export default function TeacherAvailability() {
  const { t, i18n } = useTranslation();
  const isHe = i18n.language === "he";
  const dayLabels = isHe
    ? ["א'", "ב'", "ג'", "ד'", "ה'", "ו'", "ש'"]
    : ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];

  const { id: idParam } = useParams<{ id: string }>();
  const teacherId = Number(idParam);
  const qc = useQueryClient();
  const { currentId: schoolId } = useCurrentSchool();

  const { data: teacher } = useQuery({
    queryKey: ["teacher", teacherId],
    queryFn: () => api.teachers.get(teacherId),
    enabled: !!teacherId,
  });

  const { data: timeGrid } = useQuery({
    queryKey: ["time-grid", schoolId],
    queryFn: () => api.schools.getTimeGrid(schoolId!),
    enabled: schoolId !== null,
  });

  const { data: allTeachers } = useQuery({
    queryKey: ["teachers", schoolId],
    queryFn: () => api.teachers.list(schoolId!),
    enabled: schoolId !== null,
  });

  const { data: constraints } = useQuery({
    queryKey: ["constraints", schoolId],
    queryFn: () => api.constraints.list(schoolId!),
    enabled: schoolId !== null,
  });

  // Jours actifs et nombre de créneaux/jour depuis la grille
  const daysActive = useMemo(() => {
    if (!timeGrid) return [];
    return Array.from(new Set(timeGrid.map((s) => s.day_of_week))).sort();
  }, [timeGrid]);
  const slotsPerDay = useMemo(() => {
    if (!timeGrid) return 0;
    return Math.max(0, ...timeGrid.map((s) => s.slot_index)) + 1;
  }, [timeGrid]);

  // Set "day-slot" des positions où le prof est INDISPONIBLE
  const [unavail, setUnavail] = useState<Set<string>>(new Set());

  // Plafonds (null = pas de contrainte)
  const [maxWeek, setMaxWeek] = useState<number | "">("");
  const [maxDay, setMaxDay] = useState<number | "">("");
  const [maxConsec, setMaxConsec] = useState<number | "">("");

  // Binômes (autres profs avec qui ce prof doit toujours enseigner ensemble)
  const [partners, setPartners] = useState<number[]>([]);

  // Préférences SOFT (cocher = activer, plus le weight est haut plus c'est important)
  const [prefMorning, setPrefMorning] = useState(false);
  const [prefAfternoon, setPrefAfternoon] = useState(false);
  const [prefGroupedDays, setPrefGroupedDays] = useState(false);
  const [prefAvoidGaps, setPrefAvoidGaps] = useState(false);

  // Initialiser depuis les contraintes existantes
  useEffect(() => {
    if (!constraints) return;
    const set = new Set<string>();
    let mw: number | "" = "";
    let md: number | "" = "";
    let mc: number | "" = "";
    const partnersSet = new Set<number>();

    for (const c of constraints) {
      const p = c.parameters as any;
      if (!c.is_active) continue;

      if (c.constraint_type === "block_slot_teacher" && p.target_id === teacherId) {
        for (const d of p.days ?? []) {
          for (const s of p.slot_indices ?? []) {
            set.add(`${d}-${s}`);
          }
        }
      } else if (c.constraint_type === "teacher_max_hours_week" && p.teacher_id === teacherId) {
        mw = p.max_hours;
      } else if (c.constraint_type === "teacher_max_hours_day" && p.teacher_id === teacherId) {
        md = p.max_hours;
      } else if (c.constraint_type === "teacher_max_consecutive" && p.teacher_id === teacherId) {
        mc = p.max_consecutive;
      } else if (c.constraint_type === "teachers_must_teach_together" && Array.isArray(p.teacher_ids) && p.teacher_ids.includes(teacherId)) {
        for (const tid of p.teacher_ids) {
          if (tid !== teacherId) partnersSet.add(tid);
        }
      } else if (c.constraint_type === "teacher_prefer_morning" && p.teacher_id === teacherId) {
        setPrefMorning(true);
      } else if (c.constraint_type === "teacher_prefer_afternoon" && p.teacher_id === teacherId) {
        setPrefAfternoon(true);
      } else if (c.constraint_type === "teacher_prefer_grouped_days" && p.teacher_id === teacherId) {
        setPrefGroupedDays(true);
      } else if (c.constraint_type === "teacher_avoid_gaps" && p.teacher_id === teacherId) {
        setPrefAvoidGaps(true);
      }
    }
    setUnavail(set);
    setMaxWeek(mw);
    setMaxDay(md);
    setMaxConsec(mc);
    setPartners(Array.from(partnersSet));
  }, [constraints, teacherId]);

  function toggle(day: number, slot: number) {
    const key = `${day}-${slot}`;
    setUnavail((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function toggleRow(slot: number) {
    // toggle all days for this slot
    const allInRow = daysActive.every((d) => unavail.has(`${d}-${slot}`));
    setUnavail((prev) => {
      const next = new Set(prev);
      for (const d of daysActive) {
        if (allInRow) next.delete(`${d}-${slot}`);
        else next.add(`${d}-${slot}`);
      }
      return next;
    });
  }

  function toggleDay(day: number) {
    const allInDay = Array.from({ length: slotsPerDay }).every((_, s) =>
      unavail.has(`${day}-${s}`)
    );
    setUnavail((prev) => {
      const next = new Set(prev);
      for (let s = 0; s < slotsPerDay; s++) {
        if (allInDay) next.delete(`${day}-${s}`);
        else next.add(`${day}-${s}`);
      }
      return next;
    });
  }

  const save = useMutation({
    mutationFn: async () => {
      if (!schoolId || !constraints) throw new Error("Pas d'école");

      // 1. Supprimer toutes les contraintes existantes liées à ce prof (qu'on va recréer)
      const toDelete: Constraint[] = [];
      for (const c of constraints) {
        const p = c.parameters as any;
        if (
          (c.constraint_type === "block_slot_teacher" && p.target_id === teacherId) ||
          (c.constraint_type === "teacher_max_hours_week" && p.teacher_id === teacherId) ||
          (c.constraint_type === "teacher_max_hours_day" && p.teacher_id === teacherId) ||
          (c.constraint_type === "teacher_max_consecutive" && p.teacher_id === teacherId) ||
          (c.constraint_type === "teachers_must_teach_together" &&
            Array.isArray(p.teacher_ids) &&
            p.teacher_ids.includes(teacherId)) ||
          (c.constraint_type === "teacher_prefer_morning" && p.teacher_id === teacherId) ||
          (c.constraint_type === "teacher_prefer_afternoon" && p.teacher_id === teacherId) ||
          (c.constraint_type === "teacher_prefer_grouped_days" && p.teacher_id === teacherId) ||
          (c.constraint_type === "teacher_avoid_gaps" && p.teacher_id === teacherId)
        ) {
          toDelete.push(c);
        }
      }
      for (const c of toDelete) {
        await api.constraints.remove(c.id);
      }

      // 2. Recréer indispos consolidées
      if (unavail.size > 0) {
        // Pour optimiser : grouper par (jours, slots) — pour MVP on crée 1 par cellule
        // ou plus pragmatique : 1 contrainte avec days=[unique days], slot_indices=[unique slots]
        // (le solveur appliquera le produit cartésien)
        // Pour respecter les sélections non-rectangulaires, on crée 1 contrainte par (day, slot)
        const days = Array.from(new Set(Array.from(unavail).map((k) => Number(k.split("-")[0]))));
        const slots = Array.from(new Set(Array.from(unavail).map((k) => Number(k.split("-")[1]))));
        // Si la sélection est "rectangulaire", on peut consolider
        const isRect = days.every((d) => slots.every((s) => unavail.has(`${d}-${s}`)));
        if (isRect) {
          await api.constraints.create({
            school_id: schoolId,
            constraint_type: "block_slot_teacher" as any,
            priority: "hard" as any,
            weight: null,
            parameters: { days, slot_indices: slots, target_id: teacherId },
            is_active: true,
            origin_role: "teacher" as any,
            origin_user_id: null,
            origin_description: `Disponibilités de ${teacher?.first_name ?? "?"} ${teacher?.last_name ?? ""}`,
            origin_raw_text: null,
          });
        } else {
          // 1 contrainte par (day, slot) — moins optimal mais respecte la forme exacte
          for (const key of unavail) {
            const [d, s] = key.split("-").map(Number);
            await api.constraints.create({
              school_id: schoolId,
              constraint_type: "block_slot_teacher" as any,
              priority: "hard" as any,
              weight: null,
              parameters: { days: [d], slot_indices: [s], target_id: teacherId },
              is_active: true,
              origin_role: "teacher" as any,
              origin_user_id: null,
              origin_description: `Indispo ${dayLabels[d]} créneau ${s + 1}`,
              origin_raw_text: null,
            });
          }
        }
      }

      // 3. Recréer plafonds
      if (maxWeek !== "" && maxWeek > 0) {
        await api.constraints.create({
          school_id: schoolId, constraint_type: "teacher_max_hours_week" as any,
          priority: "hard" as any, weight: null,
          parameters: { teacher_id: teacherId, max_hours: Number(maxWeek) },
          is_active: true, origin_role: "teacher" as any, origin_user_id: null,
          origin_description: null, origin_raw_text: null,
        });
      }
      if (maxDay !== "" && maxDay > 0) {
        await api.constraints.create({
          school_id: schoolId, constraint_type: "teacher_max_hours_day" as any,
          priority: "hard" as any, weight: null,
          parameters: { teacher_id: teacherId, max_hours: Number(maxDay) },
          is_active: true, origin_role: "teacher" as any, origin_user_id: null,
          origin_description: null, origin_raw_text: null,
        });
      }
      if (maxConsec !== "" && maxConsec > 0) {
        await api.constraints.create({
          school_id: schoolId, constraint_type: "teacher_max_consecutive" as any,
          priority: "hard" as any, weight: null,
          parameters: { teacher_id: teacherId, max_consecutive: Number(maxConsec) },
          is_active: true, origin_role: "teacher" as any, origin_user_id: null,
          origin_description: null, origin_raw_text: null,
        });
      }

      // 4. Co-enseignants
      if (partners.length > 0) {
        await api.constraints.create({
          school_id: schoolId, constraint_type: "teachers_must_teach_together" as any,
          priority: "hard" as any, weight: null,
          parameters: { teacher_ids: [teacherId, ...partners] },
          is_active: true, origin_role: "teacher" as any, origin_user_id: null,
          origin_description: `Binôme ${teacher?.first_name ?? "?"} ${teacher?.last_name ?? ""}`,
          origin_raw_text: null,
        });
      }

      // 5. Préférences SOFT
      const prefsToCreate: { type: string; weight: number; desc: string }[] = [];
      if (prefMorning) prefsToCreate.push({ type: "teacher_prefer_morning", weight: 10, desc: "מעדיף בוקר" });
      if (prefAfternoon) prefsToCreate.push({ type: "teacher_prefer_afternoon", weight: 10, desc: "מעדיף אחר הצהריים" });
      if (prefGroupedDays) prefsToCreate.push({ type: "teacher_prefer_grouped_days", weight: 20, desc: "ימים מרוכזים" });
      if (prefAvoidGaps) prefsToCreate.push({ type: "teacher_avoid_gaps", weight: 5, desc: "בלי חלונות" });
      for (const pref of prefsToCreate) {
        await api.constraints.create({
          school_id: schoolId, constraint_type: pref.type as any,
          priority: "soft" as any, weight: pref.weight,
          parameters: { teacher_id: teacherId },
          is_active: true, origin_role: "teacher" as any, origin_user_id: null,
          origin_description: pref.desc, origin_raw_text: null,
        });
      }
    },
    onSuccess: () => {
      toast.success("✓ נשמר");
      qc.invalidateQueries({ queryKey: ["constraints", schoolId] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  if (!teacher) return <p className="text-slate-500">{t("actions.loading")}</p>;

  const nUnavail = unavail.size;
  const totalSlots = daysActive.length * slotsPerDay;

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <Link to="/teachers" className="text-sm text-primary-600 hover:underline inline-flex items-center gap-1">
            <ArrowLeftIcon className="h-4 w-4" />
            {t("nav.teachers")}
          </Link>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
            {teacher.first_name} {teacher.last_name}
          </h1>
          <p className="text-sm text-slate-500">{teacher.code} · {teacher.email ?? "—"}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="info">
            {totalSlots - nUnavail} / {totalSlots} זמין
          </Badge>
          <Button onClick={() => save.mutate()} loading={save.isPending}>
            {t("actions.save")}
          </Button>
        </div>
      </header>

      {/* Grille indispo */}
      <Card>
        <CardHeader>
          <h2 className="font-semibold">
            📅 {isHe ? "מסלול שבועי — לחץ כדי לסמן כלא זמין" : "Disponibilités — clic pour basculer"}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {isHe
              ? "אדום = לא זמין. לחץ על שורה/עמודה כדי להחיל את כל היום/משבצת."
              : "Rouge = indisponible. Clic sur une ligne/colonne pour toggle tout le créneau/jour."}
          </p>
        </CardHeader>
        <CardBody>
          {daysActive.length === 0 ? (
            <p className="text-slate-500">{t("actions.loading")}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm select-none">
                <thead>
                  <tr>
                    <th className="px-2 py-2 text-center text-xs text-slate-500">#</th>
                    {daysActive.map((d) => (
                      <th
                        key={d}
                        className="px-2 py-2 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700 text-center"
                        onClick={() => toggleDay(d)}
                        title={isHe ? "החל לכל היום" : "Toggle tout le jour"}
                      >
                        {dayLabels[d]}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Array.from({ length: slotsPerDay }, (_, slot) => (
                    <tr key={slot}>
                      <td
                        className="px-2 py-2 font-medium text-center cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700"
                        onClick={() => toggleRow(slot)}
                        title={isHe ? "החל לכל המשבצת" : "Toggle tout le créneau"}
                      >
                        {slot + 1}
                      </td>
                      {daysActive.map((d) => {
                        const key = `${d}-${slot}`;
                        const isOff = unavail.has(key);
                        return (
                          <td key={d} className="p-1">
                            <button
                              type="button"
                              onClick={() => toggle(d, slot)}
                              className={`w-full h-10 rounded transition-colors text-xs ${
                                isOff
                                  ? "bg-red-500 hover:bg-red-600 text-white"
                                  : "bg-green-100 hover:bg-green-200 dark:bg-green-900/40 dark:hover:bg-green-900/60 text-green-700 dark:text-green-300"
                              }`}
                              aria-label={isOff ? "indispo" : "dispo"}
                            >
                              {isOff ? "✗" : "✓"}
                            </button>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Plafonds horaires */}
      <Card>
        <CardHeader>
          <h2 className="font-semibold">
            ⏱️ {isHe ? "תקרות שעות" : "Plafonds horaires"}
          </h2>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Input
              type="number" min={1} max={60}
              label={isHe ? "מקסימום שעות/שבוע" : "Max heures/semaine"}
              value={maxWeek}
              onChange={(e) => setMaxWeek(e.target.value ? Number(e.target.value) : "")}
              placeholder={isHe ? "ללא הגבלה" : "Aucun"}
            />
            <Input
              type="number" min={1} max={12}
              label={isHe ? "מקסימום שעות/יום" : "Max heures/jour"}
              value={maxDay}
              onChange={(e) => setMaxDay(e.target.value ? Number(e.target.value) : "")}
              placeholder={isHe ? "ללא הגבלה" : "Aucun"}
            />
            <Input
              type="number" min={1} max={10}
              label={isHe ? "מקסימום שיעורים ברצף" : "Max cours consécutifs"}
              value={maxConsec}
              onChange={(e) => setMaxConsec(e.target.value ? Number(e.target.value) : "")}
              placeholder={isHe ? "ללא הגבלה" : "Aucun"}
            />
          </div>
        </CardBody>
      </Card>

      {/* Binômes co-enseignants */}
      <Card>
        <CardHeader>
          <h2 className="font-semibold">
            👥 {isHe ? "מורים-שותפים (חייבים ללמד יחד)" : "Co-enseignants (doivent enseigner ensemble)"}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {isHe
              ? "המורים שיתווספו פה יחויבו ללמד באותם משבצות זמן כמו המורה הנוכחי."
              : "Les profs ajoutés ici devront toujours enseigner aux mêmes créneaux que le prof courant."}
          </p>
        </CardHeader>
        <CardBody>
          <MultiSelect
            options={(allTeachers ?? [])
              .filter((t) => t.id !== teacherId)
              .map((t) => ({ value: t.id, label: `${t.code} — ${t.first_name} ${t.last_name}` }))}
            selected={partners}
            onChange={setPartners}
            placeholder={isHe ? "אין שותפים — לחץ לבחור" : "Aucun — cliquer pour choisir"}
          />
        </CardBody>
      </Card>

      {/* Préférences SOFT */}
      <Card>
        <CardHeader>
          <h2 className="font-semibold">
            ⭐ {isHe ? "העדפות (soft)" : "Préférences (SOFT)"}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {isHe
              ? "אלה הן העדפות, לא חוקים. הפותר ינסה לכבד אותן עד כמה שאפשר אך עלול להתעלם מהן אם אין פתרון."
              : "Ce sont des préférences, pas des règles. Le solveur essaie de les respecter au mieux."}
          </p>
        </CardHeader>
        <CardBody>
          <div className="space-y-2">
            <label className="flex items-center gap-3 cursor-pointer p-2 rounded hover:bg-slate-50 dark:hover:bg-slate-700/30">
              <input type="checkbox" checked={prefMorning}
                onChange={(e) => { setPrefMorning(e.target.checked); if (e.target.checked) setPrefAfternoon(false); }}
                className="h-4 w-4 rounded border-slate-300 text-primary-600" />
              <div>
                <div className="font-medium">🌅 {isHe ? "מעדיף ללמד בבוקר" : "Préfère enseigner le matin"}</div>
                <div className="text-xs text-slate-500">{isHe ? "פנליטי על שיעורים אחרי משבצת 5" : "Pénalise les cours après le créneau 5"}</div>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer p-2 rounded hover:bg-slate-50 dark:hover:bg-slate-700/30">
              <input type="checkbox" checked={prefAfternoon}
                onChange={(e) => { setPrefAfternoon(e.target.checked); if (e.target.checked) setPrefMorning(false); }}
                className="h-4 w-4 rounded border-slate-300 text-primary-600" />
              <div>
                <div className="font-medium">🌇 {isHe ? "מעדיף ללמד אחר הצהריים" : "Préfère enseigner l'après-midi"}</div>
                <div className="text-xs text-slate-500">{isHe ? "פנליטי על שיעורים לפני משבצת 5" : "Pénalise les cours avant le créneau 5"}</div>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer p-2 rounded hover:bg-slate-50 dark:hover:bg-slate-700/30">
              <input type="checkbox" checked={prefGroupedDays}
                onChange={(e) => setPrefGroupedDays(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-primary-600" />
              <div>
                <div className="font-medium">📦 {isHe ? "ימי עבודה מרוכזים" : "Jours de travail groupés"}</div>
                <div className="text-xs text-slate-500">{isHe ? "מנסה לרכז שיעורים על 3 ימים במקום 5" : "Tente de concentrer sur 3 jours plutôt que 5"}</div>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer p-2 rounded hover:bg-slate-50 dark:hover:bg-slate-700/30">
              <input type="checkbox" checked={prefAvoidGaps}
                onChange={(e) => setPrefAvoidGaps(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-primary-600" />
              <div>
                <div className="font-medium">🚫 {isHe ? "בלי חלונות" : "Éviter les trous"}</div>
                <div className="text-xs text-slate-500">{isHe ? "מעדיף שיעורים רצופים בלי שעות פנויות באמצע" : "Préfère des cours continus sans heures vides au milieu"}</div>
              </div>
            </label>
          </div>
        </CardBody>
      </Card>

      <div className="flex justify-end">
        <Button onClick={() => save.mutate()} loading={save.isPending} size="lg">
          {t("actions.save")}
        </Button>
      </div>
    </div>
  );
}
