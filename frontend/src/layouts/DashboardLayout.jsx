import { Outlet } from 'react-router';

import { AppLayout } from '@/layouts/base/AppLayout';
import { ProtectedLayout } from '@/layouts/base/ProtectedLayout';

export const DashboardLayout = () => {
  const isSevenScreen = import.meta.env.VITE_SEVEN_SCREEN_DASHBOARD_LAYOUT_ENABLED === 'true';

  return (
    <ProtectedLayout>
      {isSevenScreen ? (
        <Outlet />
      ) : (
        <AppLayout>
          <Outlet />
        </AppLayout>
      )}
    </ProtectedLayout>
  );
};
