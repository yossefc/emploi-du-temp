import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';
import { store } from './store';

// Pages
import Dashboard from './pages/Dashboard';
import SchedulePage from './pages/Schedule';
import TeachersPage from './pages/Teachers';
import SubjectsPage from './pages/Subjects';
import ClassesPage from './pages/Classes';
import RoomsPage from './pages/Rooms';
import ScheduleGenerationPage from './pages/ScheduleGeneration';
import ImportDataPage from './pages/ImportData';

// Create a query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <div className="min-h-screen bg-gray-50">
          <Router>
            <Routes>
              {/* Routes directes sans authentification */}
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/schedule" element={<SchedulePage />} />
              <Route path="/teachers" element={<TeachersPage />} />
              <Route path="/subjects" element={<SubjectsPage />} />
              <Route path="/classes" element={<ClassesPage />} />
              <Route path="/rooms" element={<RoomsPage />} />
              <Route path="/schedule-generation" element={<ScheduleGenerationPage />} />
              <Route path="/import" element={<ImportDataPage />} />
              
              <Route
                path="/constraints"
                element={
                  <div className="flex items-center justify-center min-h-screen">
                    <div className="text-center">
                      <h1 className="text-2xl font-bold text-gray-900">Page Contraintes</h1>
                      <p className="text-gray-600 mt-2">À implémenter</p>
                    </div>
                  </div>
                }
              />
              
              <Route
                path="/settings"
                element={
                  <div className="flex items-center justify-center min-h-screen">
                    <div className="text-center">
                      <h1 className="text-2xl font-bold text-gray-900">Page Paramètres</h1>
                      <p className="text-gray-600 mt-2">À implémenter</p>
                    </div>
                  </div>
                }
              />
              
              {/* Route par défaut - redirection vers dashboard */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
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