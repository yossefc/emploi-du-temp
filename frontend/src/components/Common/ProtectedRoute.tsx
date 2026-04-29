import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { setUser } from '../../store/slices/authSlice';
import api from '../../services/api';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const location = useLocation();
  const dispatch = useAppDispatch();
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  const [hydrating, setHydrating] = useState<boolean>(
    !isAuthenticated && !!localStorage.getItem('access_token')
  );

  useEffect(() => {
    if (isAuthenticated || !localStorage.getItem('access_token')) {
      setHydrating(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const response = await api.getCurrentUser();
        if (!cancelled) dispatch(setUser(response.data));
      } catch {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      } finally {
        if (!cancelled) setHydrating(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, dispatch]);

  if (hydrating) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
