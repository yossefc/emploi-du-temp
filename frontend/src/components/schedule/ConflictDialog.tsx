/**
 * Modal qui affiche les contraintes en conflit (issues du MUS extrait par le solveur)
 * et permet à l'utilisateur de cocher celles à relaxer pour relancer.
 *
 * Pièce maîtresse du projet — c'est ce qui justifie toute la refonte v2.
 */

import { useState } from "react";
import { ExclamationTriangleIcon, LockClosedIcon } from "@heroicons/react/24/outline";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal, ModalBody, ModalFooter } from "@/components/ui/Modal";
import type { ConstraintConflictInfo } from "@/lib/types";

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
  // Set des constraint_id (non-null) que l'utilisateur veut relaxer
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

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

  function handleRetry() {
    onRetry(Array.from(selectedIds));
  }

  return (
    <Modal open={open} onClose={onClose} title="Conflit de contraintes" size="lg">
      <ModalBody>
        <div className="space-y-4">
          <div className="flex items-start gap-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/50 p-4">
            <ExclamationTriangleIcon className="h-6 w-6 flex-shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-amber-900 dark:text-amber-200">
                Le solveur n'a pas trouvé de planning satisfaisant toutes les contraintes.
              </p>
              <p className="mt-1 text-amber-700 dark:text-amber-300">
                Voici le sous-ensemble <strong>minimal</strong> de {conflicts.length}{" "}
                contrainte(s) responsables. Cochez celles que vous acceptez de relaxer
                puis relancez la génération.
              </p>
              <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
                Calculé en {(solverTimeSeconds * 1000).toFixed(0)} ms.
              </p>
            </div>
          </div>

          {/* Contraintes relaxables (avec checkbox) */}
          {relaxable.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                Contraintes modifiables ({relaxable.length})
              </h3>
              <ul className="space-y-2">
                {relaxable.map((c) => (
                  <li
                    key={c.constraint_id}
                    className="flex items-start gap-3 rounded-lg border border-slate-200 dark:border-slate-700 p-3 hover:bg-slate-50 dark:hover:bg-slate-700/30"
                  >
                    <input
                      type="checkbox"
                      id={`conflict-${c.constraint_id}`}
                      checked={selectedIds.has(c.constraint_id!)}
                      onChange={() => toggle(c.constraint_id!)}
                      className="mt-1 h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                    />
                    <label
                      htmlFor={`conflict-${c.constraint_id}`}
                      className="flex-1 cursor-pointer"
                    >
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-slate-900 dark:text-slate-100">
                          {c.title}
                        </span>
                        <Badge variant="info">#{c.constraint_id}</Badge>
                        <Badge variant="default">{c.constraint_type}</Badge>
                      </div>
                      <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                        {c.detail}
                      </p>
                      <p className="mt-1 text-xs text-slate-500 dark:text-slate-500 italic">
                        Origine : {c.origin}
                      </p>
                    </label>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Contraintes système (informationnel, non-cochables) */}
          {systemic.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                Contraintes système ({systemic.length}) — non modifiables ici
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Ces contraintes proviennent de la structure de l'école (volumes horaires
                des groupes, qualification des profs…). Pour les modifier, éditez le
                Group correspondant.
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
                          {c.title}
                        </span>
                        <Badge variant="default">{c.constraint_type}</Badge>
                      </div>
                      <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                        {c.detail}
                      </p>
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
          Annuler
        </Button>
        <Button
          variant="primary"
          onClick={handleRetry}
          loading={retrying}
          disabled={selectedIds.size === 0}
        >
          Relaxer {selectedIds.size} contrainte(s) et relancer
        </Button>
      </ModalFooter>
    </Modal>
  );
}
