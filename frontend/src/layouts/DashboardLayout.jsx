import { Outlet } from 'react-router';
import { Box } from '@mui/material';

import { AppLayout } from '@/layouts/base/AppLayout';
import { ProtectedLayout } from '@/layouts/base/ProtectedLayout';

export const DashboardLayout = () => {
  const isSevenScreen = import.meta.env.VITE_SEVEN_SCREEN_DASHBOARD_LAYOUT_ENABLED === 'true';

  return (
    <ProtectedLayout>
      {isSevenScreen ? (
        <Outlet />
      ) : (
        <Box sx={{ p: 0, m: 0 }}>
          <AppLayout>
            <Outlet />
          </AppLayout>
        </Box>
      )}
    </ProtectedLayout>
  );
};
