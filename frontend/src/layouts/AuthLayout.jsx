import { Container, Typography } from '@mui/material';
import { Outlet } from 'react-router';

import { GuestLayout } from '@/layouts/base/GuestLayout';

export const AuthLayout = () => {
  return (
    <GuestLayout>
      <Container
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '87vh',
        }}
        maxWidth='xs'
      >
        <Typography variant='h4' fontWeight={700} color='primary' letterSpacing={-0.25} mb={2}>
          {import.meta.env.VITE_APP_NAME}
        </Typography>
        <Outlet />
      </Container>
    </GuestLayout>
  );
};
