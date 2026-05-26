/**
 * Modal qui affiche les contraintes en conflit (MUS) + SUGGESTIONS d'action
 * concrètes pour les résoudre.
 *
 * Pièce maîtresse du projet — texte bilingue HE/FR, suggestions actionnables.
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import toast from "react-hot-toast";
import {
  ExclamationTriangleIcon,
  LockClosedIcon,
  LightBulbIcon,
} from "@heroicons/react/24/outline";

import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal, ModalBody, ModalFooter } from "@/components/ui/Modal";
import { api } from "@/lib/api";
import type { ConflictSuggestion, ConstraintConflictInfo } from "@/lib/types";


interface ConflictDialogProps {
  open: boolean;
  conflicts: ConstraintConflictInfo[];
  solverTimeSeconds: number;
  onClose: () => void;
  onRetry: (disabledIds: number[]) => void;
  retrying?: boolean;
}

export function ConflictDialog({
  open,
  conflicts,
  solverTimeSeconds,
  onClose,
  onRetry,
  retrying,
}: ConflictDialogProps) {
  const { t, i18n } = useTranslation();
  const isHe = i18n.language === "he";

  // Set des constraint_id (non-null) que l'utilisateur veut relaxer
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [applying, setApplying] = useState<string | null>(null);

  const relaxable = conflicts.filter((c) => c.constraint_id !== null);
  const systemic = conflicts.filter((c) => c.constraint_id === null);

  function toggle(id: number) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function pickText(he: string, fr: string): string {
    return isHe ? he : fr;
  }

  async function applySuggestion(s: ConflictSuggestion, ckey: string) {
    if (!s.auto_action) return;
    setApplying(ckey);
    try {
      const a = s.auto_action;
      if (a.verb === "patch_constraint") {
        await api.constraints.update(a.target_id, a.patch ?? {});
      } else if (a.verb === "patch_group") {
        await api.groups.update(a.target_id, a.patch ?? {});
      } else if (a.verb === "delete_constraint") {
        await api.constraints.remove(a.target_id);
      }
      toast.success(t("actions.apply") + " ✓");
      // Auto-retry with current selections
      onRetry(Array.from(selectedIds));
    } catch (e) {
      toast.error(String(e));
    } finally {
      setApplying(null);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t("conflict.title")} size="lg">
      <ModalBody>
        <div className="space-y-4">
          <div className="flex items-start gap-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/50 p-4">
            <ExclamationTriangleIcon className="h-6 w-6 flex-shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-amber-900 dark:text-amber-200">
                {t("conflict.intro_a")}
              </p>
              <p className="mt-1 text-amber-700 dark:text-amber-300">
                {t("conflict.intro_b", { n: conflicts.length })}
              </p>
              <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
                {t("conflict.calculated_in", { ms: (solverTimeSeconds * 1000).toFixed(0) })}
              </p>
            </div>
          </div>

          {/* Contraintes relaxables (avec checkbox + suggestions) */}
          {relaxable.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                {t("conflict.modifiable", { n: relaxable.length })}
              </h3>
              <ul className="space-y-3">
                {relaxable.map((c) => {
                  const ckey = `c-${c.constraint_id}`;
                  return (
                    <li
                      key={c.constraint_id}
                      className="rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden"
                    >
                      <div className="flex items-start gap-3 p-3 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700/30">
                        <input
                          type="checkbox"
                          id={ckey}
                          checked={selectedIds.has(c.constraint_id!)}
                          onChange={() => toggle(c.constraint_id!)}
                          className="mt-1 h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                        />
                        <label htmlFor={ckey} className="flex-1 cursor-pointer">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium text-slate-900 dark:text-slate-100">
                              {pickText(c.title_he, c.title_fr)}
                            </span>
                            <Badge variant="info">#{c.constraint_id}</Badge>
                            <Badge variant="default">{t(`constraint_type.${c.constraint_type}`, c.constraint_type)}</Badge>
                          </div>
                          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                            {pickText(c.detail_he, c.detail_fr)}
                          </p>
                          <p className="mt-1 text-xs text-slate-500 dark:text-slate-500 italic">
                            {t("conflict.origin", { origin: c.origin })}
                          </p>
                        </label>
                      </div>

                      {/* Suggestions */}
                      <div className="border-t border-slate-200 dark:border-slate-700 bg-blue-50/50 dark:bg-blue-900/10 p-3">
                        <div className="flex items-center gap-2 mb-2 text-sm font-medium text-blue-900 dark:text-blue-300">
                          <LightBulbIcon className="h-4 w-4" />
                          {t("conflict.suggestions_label")}
                        </div>
                        {c.suggestions.length === 0 ? (
                          <p className="text-xs text-slate-500 italic">
                            {t("conflict.no_suggestions")}
                          </p>
                        ) : (
                          <ul className="space-y-2">
                            {c.suggestions.map((s, i) => (
                              <li
                                key={i}
                                className="flex items-start justify-between gap-3 rounded-md bg-white dark:bg-slate-800 p-2 border border-blue-100 dark:border-blue-900/30"
                              >
                                <div className="flex-1 min-w-0">
                                  <div className="font-medium text-sm text-slate-900 dark:text-slate-100">
                                    {pickText(s.title_he, s.title_fr)}
                                  </div>
                                  <div className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                                    {pickText(s.description_he, s.description_fr)}
                                  </div>
                                </div>
                                {s.auto_action && (
                                  <Button
                                    size="sm"
                                    variant="secondary"
                                    onClick={() => applySuggestion(s, ckey)}
                                    loading={applying === ckey}
                                  >
                                    {t("actions.apply")}
                                  </Button>
                                )}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {/* Contraintes système (informationnel) */}
          {systemic.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                {t("conflict.systemic", { n: systemic.length })}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {t("conflict.systemic_hint")}
              </p>
              <ul className="space-y-2">
                {systemic.map((c, i) => (
                  <li
                    key={`sys-${i}`}
                    className="flex items-start gap-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/30 p-3"
                  >
                    <LockClosedIcon className="h-4 w-4 mt-1 text-slate-400" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-slate-900 dark:text-slate-100">
                          {pickText(c.title_he, c.title_fr)}
                        </span>
                        <Badge variant="default">{t(`constraint_type.${c.constraint_type}`, c.constraint_type)}</Badge>
                      </div>
                      <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                        {pickText(c.detail_he, c.detail_fr)}
                      </p>
                      {c.suggestions.length > 0 && (
                        <div className="mt-2 text-xs text-blue-700 dark:text-blue-300">
                          💡{" "}
                          {c.suggestions
                            .map((s) => pickText(s.title_he, s.title_fr))
                            .join(" · ")}
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </ModalBody>
      <ModalFooter>
        <Button variant="secondary" onClick={onClose}>
          {t("actions.cancel")}
        </Button>
        <Button
          variant="primary"
          onClick={() => onRetry(Array.from(selectedIds))}
          loading={retrying}
          disabled={selectedIds.size === 0}
        >
          {t("conflict.retry_label", { n: selectedIds.size })}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
