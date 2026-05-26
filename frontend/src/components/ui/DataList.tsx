/**
 * DataList générique : tableau responsive avec rendu personnalisable + actions.
 * Utilisé par toutes les pages CRUD.
 */

import { useTranslation } from "react-i18next";
import { TrashIcon } from "@heroicons/react/24/outline";

export interface Column<T> {
  key: string;
  label: string;
  render?: (row: T) => React.ReactNode;
  width?: string;
}

interface DataListProps<T extends { id: number }> {
  data: T[] | undefined;
  columns: Column<T>[];
  loading?: boolean;
  emptyMessage?: string;
  onDelete?: (row: T) => void;
  deletingId?: number | null;
}

export function DataList<T extends { id: number }>({
  data,
  columns,
  loading,
  emptyMessage,
  onDelete,
  deletingId,
}: DataListProps<T>) {
  const { t } = useTranslation();

  if (loading) {
    return <p className="text-slate-500 p-4 text-center">{t("actions.loading")}</p>;
  }
  if (!data || data.length === 0) {
    return (
      <p className="text-slate-500 p-8 text-center">
        {emptyMessage ?? t("actions.no_data")}
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-50 dark:bg-slate-900/50">
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                style={c.width ? { width: c.width } : undefined}
                className="px-3 py-2 text-start font-medium text-slate-600 dark:text-slate-300"
              >
                {c.label}
              </th>
            ))}
            {onDelete && <th className="w-12" />}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr
              key={row.id}
              className="border-t border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/30"
            >
              {columns.map((c) => (
                <td key={c.key} className="px-3 py-2 align-top">
                  {c.render ? c.render(row) : (row as any)[c.key]}
                </td>
              ))}
              {onDelete && (
                <td className="px-2 py-1 text-center">
                  <button
                    type="button"
                    onClick={() => {
                      if (confirm(t("actions.delete") + " ?")) onDelete(row);
                    }}
                    disabled={deletingId === row.id}
                    className="text-red-500 hover:text-red-700 disabled:opacity-50"
                    aria-label={t("actions.delete")}
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
