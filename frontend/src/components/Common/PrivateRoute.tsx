import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAppSelector } from '../../store/hooks';
import { CircularProgress, Box } from '@mui/material';

interface PrivateRouteProps {
  children: React.ReactNode;
  requiredRole?: 'admin' | 'teacher' | 'viewer';
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ children, requiredRole }) => {
  const { isAuthenticated, user, isLoading } = useAppSelector(state => state.auth);

  // Si on est en train de charger l'état d'authentification
  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh'
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // Si l'utilisateur n'est pas authentifié
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Si un rôle spécifique est requis et que l'utilisateur ne l'a pas
  if (requiredRole && user?.role !== requiredRole && user?.role !== 'admin') {
    return <Navigate to="/unauthorized" replace />;
  }

  // L'utilisateur est authentifié et a les permissions nécessaires
  return <>{children}</>;
};

export default PrivateRoute; 