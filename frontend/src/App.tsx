import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';
import { store } from './store';

// Pages
import LoginPage from './pages/Login';
import Dashboard from './pages/Dashboard';
import SchedulePage from './pages/Schedule';

// Components
import PrivateRoute from './components/Common/PrivateRoute';

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
  useEffect(() => {
    // Vérifier si un token existe au chargement de l'app
    const token = localStorage.getItem('access_token');
    if (token) {
      // TODO: Valider le token et récupérer les infos utilisateur
      // dispatch(validateToken());
    }
  }, []);

  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <div className="min-h-screen bg-gray-50">
          <Router>
            <Routes>
              {/* Routes publiques */}
              <Route path="/login" element={<LoginPage />} />
              
              {/* Routes protégées */}
              <Route
                path="/dashboard"
                element={
                  <PrivateRoute>
                    <Dashboard />
                  </PrivateRoute>
                }
              />
              
              <Route
                path="/schedule"
                element={
                  <PrivateRoute>
                    <SchedulePage />
                  </PrivateRoute>
                }
              />
              
              {/* Routes à implémenter */}
              <Route
                path="/teachers"
                element={
                  <PrivateRoute>
                    <div className="flex items-center justify-center min-h-screen">
                      <div className="text-center">
                        <h1 className="text-2xl font-bold text-gray-900">Page Enseignants</h1>
                        <p className="text-gray-600 mt-2">À implémenter</p>
                      </div>
                    </div>
                  </PrivateRoute>
                }
              />
              
              <Route
                path="/subjects"
                element={
                  <PrivateRoute>
                    <div className="flex items-center justify-center min-h-screen">
                      <div className="text-center">
                        <h1 className="text-2xl font-bold text-gray-900">Page Matières</h1>
                        <p className="text-gray-600 mt-2">À implémenter</p>
                      </div>
                    </div>
                  </PrivateRoute>
                }
              />
              
              <Route
                path="/classes"
                element={
                  <PrivateRoute>
                    <div className="flex items-center justify-center min-h-screen">
                      <div className="text-center">
                        <h1 className="text-2xl font-bold text-gray-900">Page Classes</h1>
                        <p className="text-gray-600 mt-2">À implémenter</p>
                      </div>
                    </div>
                  </PrivateRoute>
                }
              />
              
              <Route
                path="/rooms"
                element={
                  <PrivateRoute>
                    <div className="flex items-center justify-center min-h-screen">
                      <div className="text-center">
                        <h1 className="text-2xl font-bold text-gray-900">Page Salles</h1>
                        <p className="text-gray-600 mt-2">À implémenter</p>
                      </div>
                    </div>
                  </PrivateRoute>
                }
              />
              
              <Route
                path="/constraints"
                element={
                  <PrivateRoute requiredRole="admin">
                    <div className="flex items-center justify-center min-h-screen">
                      <div className="text-center">
                        <h1 className="text-2xl font-bold text-gray-900">Page Contraintes</h1>
                        <p className="text-gray-600 mt-2">À implémenter (Admin seulement)</p>
                      </div>
                    </div>
                  </PrivateRoute>
                }
              />
              
              <Route
                path="/settings"
                element={
                  <PrivateRoute>
                    <div className="flex items-center justify-center min-h-screen">
                      <div className="text-center">
                        <h1 className="text-2xl font-bold text-gray-900">Page Paramètres</h1>
                        <p className="text-gray-600 mt-2">À implémenter</p>
                      </div>
                    </div>
                  </PrivateRoute>
                }
              />
              
              {/* Route par défaut */}
              <Route path="/" element={<Navigate to="/login" replace />} />
              
              {/* Route 404 */}
              <Route
                path="*"
                element={
                  <div className="flex items-center justify-center min-h-screen">
                    <div className="text-center">
                      <h1 className="text-4xl font-bold text-gray-900">404</h1>
                      <p className="text-gray-600 mt-2">Page non trouvée</p>
                      <p className="text-gray-500 text-sm mt-1">La page que vous recherchez n'existe pas.</p>
                    </div>
                  </div>
                }
              />
            </Routes>
          </Router>
          
          {/* Toast notifications */}
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#4ade80',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 5000,
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </div>
        
        {/* React Query Devtools */}
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </Provider>
  );
}

export default App; 