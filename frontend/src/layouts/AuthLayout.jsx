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
          width: '100%',
          background: 'linear-gradient(to right, #e0eafc, #cfdef3)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          paddingTop: '10vh'
        }}
      >
        <Container
          maxWidth="sm"
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'white',
            borderRadius: 2,
            boxShadow: 3,
            p: 5,
            width: '500px'
          }}
        >
          <Typography 
            variant='h4' 
            fontWeight={700} 
            color='primary' 
            letterSpacing={-0.25} 
            mb={4}
            sx={{ mt: -1 }}
          >
            {import.meta.env.VITE_APP_NAME}
          </Typography>
          <Outlet />
        </Container>
      </Box>
    </GuestLayout>
  );
};
