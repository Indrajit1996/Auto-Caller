import { useState } from 'react';

import { yupResolver } from '@hookform/resolvers/yup'; 
import { Alert, Button, Divider, Grid2 as Grid, TextField, Typography } from '@mui/material';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router';
import { Link as RouterLink } from 'react-router';
import * as yup from 'yup';

import { ForgotPasswordDialog } from '@/components/Dialogs/ForgotPasswordDialog';
import PasswordField from '@/components/PasswordField';
import { ROUTES } from '@/constants/routeConstants';
import { useAuth } from '@/hooks';

export const Login = () => {
  const loginSchema = yup.object().shape({
    email: yup.string().email('Invalid email format').required('Email is required'),
    password: yup.string().required('Password is required'),
  });

  const [isForgotPasswordOpen, setIsForgotPasswordOpen] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const [alertData, setAlertData] = useState();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: yupResolver(loginSchema),
  });

  const onSubmit = async (data) => {
    const formData = new URLSearchParams();
    formData.append('username', data.email);
    formData.append('password', data.password);

    try {
      await login(formData);
    } catch (error) {
      setMessage(error?.message?.title + '. ' + error?.message?.message);
    }
  };

  const handleOpenForgotPassword = () => {
    setIsForgotPasswordOpen(true);
  };

  const handleCloseForgotPassword = () => {
    setIsForgotPasswordOpen(false);
  };

  const renderAuthAlert = () => {
    if (alertData) {
      const { message, severity, status } = alertData;

      return (
        <>
          {message ? (
            <Alert
              severity={severity}
              sx={{
                width: '100%',
                mb: 2,
                alignItems: 'center',
              }}
              onClose={() => setAlertData(null)}
              action={
                status === 'PENDING_EMAIL_VERIFICATION' && (
                  <Button
                    color='inherit'
                    component={RouterLink}
                    to={ROUTES.AUTH.VERIFY_EMAIL}
                    variant='outlined'
                  >
                    Resend
                  </Button>
                )
              }
            >
              {message}
            </Alert>
          ) : (
            <Alert
              severity='error'
              sx={{
                width: '100%',
                mb: 2,
              }}
              onClose={() => setAlertData(null)}
            >
              An error occurred. Please try again.
            </Alert>
          )}
        </>
      );
    }
  };

  return (
    <>
      <Typography component='h1' variant='h5' align='center' sx={{ mb: 4 }}>
        Sign in to your account
      </Typography>
      <Grid container spacing={2} component='form' noValidate onSubmit={handleSubmit(onSubmit)}>
        {renderAuthAlert()}
        <TextField
          variant='outlined'
          required
          fullWidth
          id='email'
          label='Email Address'
          autoComplete='email'
          autoFocus
          {...register('email')}
          error={!!errors.email}
          helperText={errors.email?.message}
        />
        <PasswordField
          fullWidth
          required
          label='Password'
          id='password'
          autoComplete='current-password'
          {...register('password')}
          error={!!errors.password}
          helperText={errors.password?.message}
        />
        <Button type='submit' fullWidth variant='contained' color='primary' sx={{ mt: 2 }}>
          Login
        </Button>
        <Button onClick={handleOpenForgotPassword} fullWidth variant='text' color='primary'>
          Forgot password?
        </Button>
        <Divider sx={{ my: 2, width: '100%' }} />
        <Button
          type='button'
          fullWidth
          variant='outlined'
          color='primary'
          onClick={() => navigate('/register')}
        >
          Create a new account
        </Button>
      </Grid>
      <ForgotPasswordDialog open={isForgotPasswordOpen} onClose={handleCloseForgotPassword} />
    </>
  );
};
