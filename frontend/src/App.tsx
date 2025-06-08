import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Provider } from 'react-redux';
import { store } from './store';

// Pages
import LoginPage from './pages/Login';
import Dashboard from './pages/Dashboard';
import SchedulePage from './pages/Schedule';

// Components
import PrivateRoute from './components/Common/PrivateRoute';

// Theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#2196f3',
    },
    secondary: {
      main: '#f50057',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
      '"Apple Color Emoji"',
      '"Segoe UI Emoji"',
      '"Segoe UI Symbol"',
    ].join(','),
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
      <ThemeProvider theme={theme}>
        <CssBaseline />
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
                  <div>Page Enseignants - À implémenter</div>
                </PrivateRoute>
              }
            />
            
            <Route
              path="/subjects"
              element={
                <PrivateRoute>
                  <div>Page Matières - À implémenter</div>
                </PrivateRoute>
              }
            />
            
            <Route
              path="/classes"
              element={
                <PrivateRoute>
                  <div>Page Classes - À implémenter</div>
                </PrivateRoute>
              }
            />
            
            <Route
              path="/rooms"
              element={
                <PrivateRoute>
                  <div>Page Salles - À implémenter</div>
                </PrivateRoute>
              }
            />
            
            <Route
              path="/constraints"
              element={
                <PrivateRoute requiredRole="admin">
                  <div>Page Contraintes - À implémenter</div>
                </PrivateRoute>
              }
            />
            
            <Route
              path="/settings"
              element={
                <PrivateRoute>
                  <div>Page Paramètres - À implémenter</div>
                </PrivateRoute>
              }
            />
            
            {/* Route par défaut */}
            <Route path="/" element={<Navigate to="/login" replace />} />
            
            {/* Route 404 */}
            <Route
              path="*"
              element={
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'center', 
                  alignItems: 'center', 
                  height: '100vh',
                  flexDirection: 'column'
                }}>
                  <h1>404 - Page non trouvée</h1>
                  <p>La page que vous recherchez n'existe pas.</p>
                </div>
              }
            />
          </Routes>
        </Router>
      </ThemeProvider>
    </Provider>
  );
}

export default App; 