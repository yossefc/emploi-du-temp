import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';
import { store } from './store';

import LoginPage from './pages/Login';
import Dashboard from './pages/Dashboard';
import SchedulePage from './pages/Schedule';
import TeachersPage from './pages/Teachers';
import SubjectsPage from './pages/Subjects';
import ClassesPage from './pages/Classes';
import RoomsPage from './pages/Rooms';
import ScheduleGenerationPage from './pages/ScheduleGeneration';
import ImportDataPage from './pages/ImportData';
import ProtectedRoute from './components/Common/ProtectedRoute';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      refetchOnWindowFocus: false,
    },
  },
});

const Stub: React.FC<{ title: string }> = ({ title }) => (
  <div className="flex items-center justify-center min-h-screen p-4">
    <div className="text-center">
      <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
      <p className="text-gray-600 mt-2">À implémenter</p>
    </div>
  </div>
);

function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <div className="min-h-screen bg-gray-50">
          <Router>
            <Routes>
              <Route path="/login" element={<LoginPage />} />

              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/schedule"
                element={
                  <ProtectedRoute>
                    <SchedulePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/teachers"
                element={
                  <ProtectedRoute>
                    <TeachersPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/subjects"
                element={
                  <ProtectedRoute>
                    <SubjectsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/classes"
                element={
                  <ProtectedRoute>
                    <ClassesPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/rooms"
                element={
                  <ProtectedRoute>
                    <RoomsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/schedule-generation"
                element={
                  <ProtectedRoute>
                    <ScheduleGenerationPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/import"
                element={
                  <ProtectedRoute>
                    <ImportDataPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/constraints"
                element={
                  <ProtectedRoute>
                    <Stub title="Page Contraintes" />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/settings"
                element={
                  <ProtectedRoute>
                    <Stub title="Page Paramètres" />
                  </ProtectedRoute>
                }
              />

              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Router>
          <Toaster position="top-right" />
          <ReactQueryDevtools initialIsOpen={false} />
        </div>
      </QueryClientProvider>
    </Provider>
  );
}

export default App;
