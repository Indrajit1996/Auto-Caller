import { Navigate } from 'react-router';

import { ROUTES } from '@/constants/routeConstants';
import { useAuth } from '@/hooks';

export const GuestLayout = ({ children }) => {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return <Navigate to={ROUTES.LOGGED_IN_HOME} replace />;
  }

  return <>{children}</>;
};
