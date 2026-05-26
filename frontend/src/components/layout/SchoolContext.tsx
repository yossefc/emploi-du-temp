/**
 * Hook pratique : récupère l'école courante (1ère par défaut) pour les pages
 * scoped. Évite la duplication du dropdown sur chaque page.
 */

import { createContext, useContext, useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { School } from "@/lib/types";


interface SchoolCtx {
  schools: School[] | undefined;
  currentId: number | null;
  setCurrentId: (id: number | null) => void;
  current: School | undefined;
  loading: boolean;
}

const Ctx = createContext<SchoolCtx | undefined>(undefined);

const LS_KEY = "current_school_id";

export function SchoolProvider({ children }: { children: React.ReactNode }) {
  const { data: schools, isLoading } = useQuery({
    queryKey: ["schools"],
    queryFn: () => api.schools.list(),
  });
  const [currentId, setCurrentId] = useState<number | null>(() => {
    const stored = localStorage.getItem(LS_KEY);
    return stored ? Number(stored) : null;
  });

  // Auto-select first school if none selected and schools loaded
  useEffect(() => {
    if (currentId === null && schools && schools.length > 0) {
      setCurrentId(schools[0].id);
    }
    if (currentId !== null && schools && !schools.find((s) => s.id === currentId)) {
      setCurrentId(schools[0]?.id ?? null);
    }
  }, [schools, currentId]);

  useEffect(() => {
    if (currentId !== null) localStorage.setItem(LS_KEY, String(currentId));
  }, [currentId]);

  const current = schools?.find((s) => s.id === currentId);

  return (
    <Ctx.Provider value={{ schools, currentId, setCurrentId, current, loading: isLoading }}>
      {children}
    </Ctx.Provider>
  );
}

export function useCurrentSchool() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useCurrentSchool must be used inside SchoolProvider");
  return ctx;
}
