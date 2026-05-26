import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { Toaster } from "react-hot-toast";

import { AppShell } from "@/components/layout/AppShell";
import Dashboard from "@/pages/Dashboard";
import Wizard from "@/pages/Wizard";
import Schedules from "@/pages/Schedules";
import ScheduleDetail from "@/pages/ScheduleDetail";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

// Placeholder pour les pages pas encore implémentées (5b.1, 5b.2, 6...)
const Stub = ({ title }: { title: string }) => (
  <div className="flex items-center justify-center min-h-[60vh]">
    <div className="text-center">
      <h1 className="text-2xl font-bold text-slate-700 dark:text-slate-300">{title}</h1>
      <p className="mt-2 text-slate-500">À implémenter dans une phase suivante</p>
    </div>
  </div>
);

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route index element={<Dashboard />} />
            <Route path="wizard" element={<Wizard />} />
            <Route path="schools" element={<Stub title="Schools (Phase 5b.2)" />} />
            <Route path="grades" element={<Stub title="Grades (Phase 5b.2)" />} />
            <Route path="classes" element={<Stub title="Classes (Phase 5b.2)" />} />
            <Route path="subjects" element={<Stub title="Subjects (Phase 5b.2)" />} />
            <Route path="teachers" element={<Stub title="Teachers (Phase 5b.2)" />} />
            <Route path="rooms" element={<Stub title="Rooms (Phase 5b.2)" />} />
            <Route path="groups" element={<Stub title="Groups (Phase 5b.2)" />} />
            <Route path="constraints" element={<Stub title="Constraints (Phase 5b.2)" />} />
            <Route path="schedules" element={<Schedules />} />
            <Route path="schedules/:id" element={<ScheduleDetail />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
