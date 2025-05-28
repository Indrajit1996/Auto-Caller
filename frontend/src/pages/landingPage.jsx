import { Button, Container, Grid2 as Grid, Typography } from '@mui/material';
import { useNavigate } from 'react-router';
import { useAuth } from '@/hooks';
import Login from './loginPage/Login';
// import Login from './auth/Login'

export const LandingPage = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const appName = import.meta.env.VITE_APP_NAME || 'Project Name';

  return (
    <> 
      <Login />
    </>
  );
};
