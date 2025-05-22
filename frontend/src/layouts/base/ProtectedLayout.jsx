import { Navigate } from 'react-router';

import { ROUTES } from '@/constants/routeConstants';
import { useAuth } from '@/hooks';

export const ProtectedLayout = ({ children }) => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.AUTH.LOGIN} replace />;
  }

  return <>{children}</>;
};
