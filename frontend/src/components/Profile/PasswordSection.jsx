import { useState } from 'react';

import { yupResolver } from '@hookform/resolvers/yup';
import { Lock as LockIcon } from '@mui/icons-material';
import { Box, Button, Typography } from '@mui/material';
import { useForm } from 'react-hook-form';
import * as yup from 'yup';

import authApi from '@/api/auth';
import PasswordField from '@/components/PasswordField';
import { useSnackbar } from '@/hooks/useSnackbar';
import { confirmNewPasswordSchema, passwordSchema } from '@/utils/validation';

const schema = yup
  .object({
    currentPassword: yup.string().required('Current password is required'),
    newPassword: passwordSchema,
    confirmPassword: confirmNewPasswordSchema,
  })
  .required();

const PasswordSection = () => {
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const { showSuccess, showError } = useSnackbar();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: yupResolver(schema),
    defaultValues: {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    },
  });

  const onSubmit = async (data) => {
    try {
      await authApi.updatePassword({
        current_password: data.currentPassword,
        new_password: data.newPassword,
      });
      reset();
      setShowPasswordForm(false);
      showSuccess('Password updated successfully');
    } catch (error) {
      showError(error.response?.data?.detail || 'Failed to update password');
    }
  };

  return (
    <Box sx={{ mb: 4 }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 4,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <LockIcon color='primary' />
          <Typography variant='h6'>Change Password</Typography>
        </Box>
        <Button
          color={showPasswordForm ? 'neutral' : 'primary'}
          variant='outlined'
          onClick={() => {
            setShowPasswordForm(!showPasswordForm);
            if (showPasswordForm) reset();
          }}
        >
          {showPasswordForm ? 'Cancel' : 'Change Password'}
        </Button>
      </Box>

      {showPasswordForm && (
        <Box
          component='form'
          onSubmit={handleSubmit(onSubmit)}
          sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}
        >
          <PasswordField
            label='Current Password'
            {...register('currentPassword')}
            error={!!errors.currentPassword}
            helperText={errors.currentPassword?.message}
            disabled={isSubmitting}
          />
          <PasswordField
            label='New Password'
            {...register('newPassword')}
            error={!!errors.newPassword}
            helperText={errors.newPassword?.message}
            disabled={isSubmitting}
          />
          <PasswordField
            label='Confirm New Password'
            {...register('confirmPassword')}
            error={!!errors.confirmPassword}
            helperText={errors.confirmPassword?.message}
            disabled={isSubmitting}
          />
          <Button
            type='submit'
            variant='contained'
            sx={{ alignSelf: 'flex-start', mt: 1 }}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Updating...' : 'Update Password'}
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default PasswordSection;
