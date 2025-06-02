import { Container, Typography } from '@mui/material';
import { Outlet } from 'react-router';
import { GuestLayout } from '@/layouts/base/GuestLayout';
import Box from '@mui/material/Box';

export const AuthLayout = () => {
  return (
    <GuestLayout>
      <Box
        sx={{
          minHeight: '100vh',
          width: '100vw',
          background: 'linear-gradient(to right, #e0eafc, #cfdef3)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Container
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            width: '100%',
            maxWidth: 500,
          }}
        >
          <Typography variant='h4' fontWeight={700} color='primary' letterSpacing={-0.25} mb={2}>
            {import.meta.env.VITE_APP_NAME}
          </Typography>
          <Outlet />
        </Container>
      </Box>
    </GuestLayout>
  );
};
