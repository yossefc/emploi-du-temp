import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAppSelector } from '../../store/hooks';

interface PrivateRouteProps {
  children: React.ReactNode;
  requiredRole?: 'admin' | 'teacher' | 'viewer';
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ children, requiredRole }) => {
  const { isAuthenticated, user, isLoading } = useAppSelector(state => state.auth);

  // Si on est en train de charger l'état d'authentification
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <svg className="animate-spin h-12 w-12 text-blue-600 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="mt-4 text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  // Si l'utilisateur n'est pas authentifié
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Si un rôle spécifique est requis et que l'utilisateur ne l'a pas
  if (requiredRole && user?.role !== requiredRole && user?.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Accès non autorisé</h1>
          <p className="text-gray-600 mt-2">Vous n'avez pas les permissions nécessaires pour accéder à cette page.</p>
          <Navigate to="/dashboard" replace />
        </div>
      </div>
    );
  }

  // L'utilisateur est authentifié et a les permissions nécessaires
  return <>{children}</>;
};

export default PrivateRoute; 