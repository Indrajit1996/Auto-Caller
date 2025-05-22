import { yupResolver } from '@hookform/resolvers/yup';
import { Button, Grid2 as Grid, TextField, Typography } from '@mui/material';
import { useForm } from 'react-hook-form';
import { useNavigate, useSearchParams } from 'react-router';
import * as yup from 'yup';

import authApi from '@/api/auth';
import { ROUTES } from '@/constants/routeConstants';
import { useSnackbar } from '@/hooks/useSnackbar';
import { confirmPasswordSchema, passwordSchema } from '@/utils/validation';

export const ResetPassword = () => {
  const resetPasswordSchema = yup.object().shape({
    password: passwordSchema,
    confirmPassword: confirmPasswordSchema,
  });

  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { showSuccess, showError } = useSnackbar();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: yupResolver(resetPasswordSchema),
    mode: 'onChange',
    defaultValues: {
      password: '',
      confirmPassword: '',
    },
    criteriaMode: 'all',
  });

  const onSubmit = async (data) => {
    try {
      const token = searchParams.get('token');
      if (!token) {
        showError('Reset token is missing');
        return;
      }

      await authApi.resetPassword({
        token,
        new_password: data.password,
      });
      showSuccess('Password reset successfully');
      navigate(ROUTES.AUTH.LOGIN);
    } catch (error) {
      showError(error?.response?.data?.detail || 'Failed to reset password');
    }
  };

  return (
    <>
      <Typography component='h1' variant='h5' align='center' sx={{ mb: 4 }}>
        Reset Password
      </Typography>

      <Grid container spacing={2} component='form' noValidate onSubmit={handleSubmit(onSubmit)}>
        <Grid size={12}>
          <TextField
            required
            fullWidth
            label='New Password'
            type='password'
            id='password'
            autoComplete='new-password'
            disabled={isSubmitting}
            {...register('password')}
            error={!!errors.password}
            helperText={errors.password?.message}
          />
        </Grid>

        <Grid size={12}>
          <TextField
            required
            fullWidth
            label='Confirm Password'
            type='password'
            id='confirmPassword'
            autoComplete='new-password'
            disabled={isSubmitting}
            {...register('confirmPassword')}
            error={!!errors.confirmPassword}
            helperText={errors.confirmPassword?.message}
          />
        </Grid>

        <Button type='submit' fullWidth variant='contained' disabled={isSubmitting} sx={{ mt: 2 }}>
          {isSubmitting ? 'Resetting Password...' : 'Reset Password'}
        </Button>
      </Grid>
    </>
  );
};
