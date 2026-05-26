/**
 * Multi-select avec checkboxes (pour M2M comme teacher_ids, source_class_ids).
 * Affichage compact en chips sélectionnées.
 */

import { useState } from "react";
import clsx from "clsx";

export interface MultiSelectOption {
  value: number;
  label: string;
}

interface Props {
  label?: string;
  options: MultiSelectOption[];
  selected: number[];
  onChange: (selected: number[]) => void;
  placeholder?: string;
}

export function MultiSelect({ label, options, selected, onChange, placeholder }: Props) {
  const [open, setOpen] = useState(false);

  function toggle(v: number) {
    const set = new Set(selected);
    if (set.has(v)) set.delete(v);
    else set.add(v);
    onChange(Array.from(set));
  }

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
          {label}
        </label>
      )}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={clsx(
          "w-full rounded-lg border bg-white dark:bg-slate-800 px-3 py-2 text-start text-base",
          "text-slate-900 dark:text-slate-100",
          "border-slate-300 dark:border-slate-600",
          "focus:outline-none focus:ring-2 focus:ring-primary-500",
          "min-h-[44px]"
        )}
      >
        {selected.length === 0 ? (
          <span className="text-slate-400">{placeholder ?? "—"}</span>
        ) : (
          <div className="flex flex-wrap gap-1">
            {selected.map((v) => {
              const o = options.find((x) => x.value === v);
              return (
                <span
                  key={v}
                  className="bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300 rounded px-2 py-0.5 text-xs"
                >
                  {o?.label ?? `#${v}`}
                </span>
              );
            })}
          </div>
        )}
      </button>
      {open && (
        <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-2 max-h-60 overflow-y-auto shadow-lg">
          {options.length === 0 && (
            <p className="text-sm text-slate-500 p-2">—</p>
          )}
          {options.map((o) => (
            <label
              key={o.value}
              className="flex items-center gap-2 p-2 rounded hover:bg-slate-50 dark:hover:bg-slate-700/30 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selected.includes(o.value)}
                onChange={() => toggle(o.value)}
                className="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm">{o.label}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
