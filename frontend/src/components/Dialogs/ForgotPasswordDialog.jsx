import { yupResolver } from '@hookform/resolvers/yup';
import Button from '@mui/material/Button';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import TextField from '@mui/material/TextField';
import { useForm } from 'react-hook-form';
import * as yup from 'yup';

import authApi from '@/api/auth';
import { PersistentDialog } from '@/components/PersistentDialog';
import { useSnackbar } from '@/hooks/useSnackbar';

export const ForgotPasswordDialog = ({ open, onClose }) => {
  const forgotPasswordSchema = yup.object().shape({
    email: yup.string().email('Invalid email address').required('Email is required'),
  });

  const { showSuccess, showError } = useSnackbar();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm({
    resolver: yupResolver(forgotPasswordSchema),
    mode: 'onChange',
    defaultValues: {
      email: '',
    },
  });

  const onSubmit = async (data) => {
    try {
      const response = await authApi.passwordRecovery(data.email);
      showSuccess(response.data.message);
      // reset();
      // onClose();
    } catch (error) {
      if (error.response) {
        if (error.response.status === 404) {
          showError(error?.response?.data?.detail);
        } else if (error?.response?.status === 422) {
          showError('Invalid email format');
        } else {
          showError(error?.response?.data?.detail || 'An error occurred');
        }
      } else {
        showError('Failed to connect to the server. Please try again');
      }
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <PersistentDialog
      open={open}
      onClose={handleClose}
      title='Reset Password'
      isForm
      onSubmit={handleSubmit(onSubmit)}
      fullWidth
    >
      <DialogContent dividers>
        <DialogContentText>
          To reset your password, please enter your email address here. We will send you
          instructions to reset your password.
        </DialogContentText>

        <TextField
          sx={{ mt: 2 }}
          autoFocus
          id='email'
          label='Email Address'
          type='email'
          fullWidth
          disabled={isSubmitting}
          {...register('email')}
          error={!!errors.email}
          helperText={errors.email?.message}
        />
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={isSubmitting} variant='outlined' color='neutral'>
          Cancel
        </Button>
        <Button type='submit' disabled={isSubmitting} color='primary' variant='contained'>
          {isSubmitting ? 'Sending...' : 'Submit'}
        </Button>
      </DialogActions>
    </PersistentDialog>
  );
};
