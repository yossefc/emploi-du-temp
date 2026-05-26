import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { Toaster } from "react-hot-toast";

import { AppShell } from "@/components/layout/AppShell";
import { SchoolProvider } from "@/components/layout/SchoolContext";
import Dashboard from "@/pages/Dashboard";
import Wizard from "@/pages/Wizard";
import Schedules from "@/pages/Schedules";
import ScheduleDetail from "@/pages/ScheduleDetail";
import Teachers from "@/pages/Teachers";
import Subjects from "@/pages/Subjects";
import Classes from "@/pages/Classes";
import Rooms from "@/pages/Rooms";
import Schools from "@/pages/Schools";
import Groups from "@/pages/Groups";
import Constraints from "@/pages/Constraints";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

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
      <SchoolProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<AppShell />}>
              <Route index element={<Dashboard />} />
              <Route path="wizard" element={<Wizard />} />
              <Route path="schools" element={<Schools />} />
              <Route path="grades" element={<Stub title="Grades" />} />
              <Route path="classes" element={<Classes />} />
              <Route path="subjects" element={<Subjects />} />
              <Route path="teachers" element={<Teachers />} />
              <Route path="rooms" element={<Rooms />} />
              <Route path="groups" element={<Groups />} />
              <Route path="constraints" element={<Constraints />} />
              <Route path="schedules" element={<Schedules />} />
              <Route path="schedules/:id" element={<ScheduleDetail />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </SchoolProvider>
      <Toaster position="top-right" />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
