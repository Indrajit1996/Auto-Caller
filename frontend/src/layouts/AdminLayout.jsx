import { Container } from '@mui/material';
import { Navigate, Outlet } from 'react-router';

import ErrorPage from '@/components/Error/ErrorPage';
import { ROUTES } from '@/constants/routeConstants';
import { useAuth } from '@/hooks';
import { AppLayout } from '@/layouts/base/AppLayout';

export const AdminLayout = () => {
  const { isSuperUser, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.AUTH.LOGIN} replace />;
  }

  if (!isSuperUser) {
    return (
      <ErrorPage
        code='403'
        title='Forbidden'
        description='You do not have permission to access this page.'
      />
    );
  }

  return (
    <AppLayout>
      <Container maxWidth='lg' sx={{ mt: 4 }}>
        <Outlet />
      </Container>
    </AppLayout>
  );
};
