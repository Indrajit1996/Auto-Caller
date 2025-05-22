import { useEffect, useState } from 'react';

import { yupResolver } from '@hookform/resolvers/yup';
import {
  Button,
  DialogActions,
  DialogContent,
  FormControl,
  FormHelperText,
  Grid2 as Grid,
  InputLabel,
  MenuItem,
  Select,
  TextField,
} from '@mui/material';
import { Controller, useForm } from 'react-hook-form';
import * as yup from 'yup';

import usersApi from '@/api/users';
import PasswordField from '@/components/PasswordField';
import { PersistentDialog } from '@/components/PersistentDialog';
import { useSnackbar } from '@/hooks/useSnackbar';
import { emailSchema, passwordSchema } from '@/utils/validation';

export const EditUserDialog = ({ open, onClose, id, onSuccess }) => {
  const [editPassword, setEditPassword] = useState(false);
  const { showSuccess, showError } = useSnackbar();

  const editUserSchema = yup.object().shape({
    email: emailSchema,
    first_name: yup
      .string()
      .max(100, 'First name must not exceed 100 characters')
      .required('First name is required'),
    last_name: yup
      .string()
      .max(100, 'Last name must not exceed 100 characters')
      .required('Last name is required'),
    role: yup.string().oneOf(['user', 'superuser'], 'Invalid role').required('Role is required'),
    ...(editPassword && {
      password: passwordSchema,
    }),
  });

  const {
    control,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
  } = useForm({
    resolver: yupResolver(editUserSchema),
  });

  useEffect(() => {
    if (open && id) {
      const fetchUser = async () => {
        try {
          const response = await usersApi.getUser(id);
          const user = response.data;
          setValue('first_name', user.first_name);
          setValue('last_name', user.last_name);
          setValue('email', user.email);
          setValue('role', user.is_superuser ? 'superuser' : 'user');
        } catch (error) {
          console.error(error);
        }
      };
      fetchUser();
    } else {
      reset();
      setEditPassword(false);
    }
  }, [open, id, setValue, reset]);

  const onSubmit = async (data) => {
    const payload = {
      first_name: data.first_name,
      last_name: data.last_name,
      is_superuser: data.role === 'superuser',
      email: data.email,
      id,
    };

    if (editPassword) {
      payload.password = data.password;
    }

    try {
      await usersApi.editUser(id, payload);
      onClose();
      showSuccess('User updated successfully');
      onSuccess?.();
    } catch (error) {
      console.error(error);
      showError(error.response?.data?.detail || 'Failed to update user');
    }
  };

  const handleCloseAndReset = () => {
    reset();
    onClose();
  };

  return (
    <PersistentDialog
      open={open}
      onClose={handleCloseAndReset}
      title='Edit User'
      onSubmit={handleSubmit(onSubmit)}
      isForm
    >
      <DialogContent dividers>
        <Grid container spacing={1}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Controller
              name='first_name'
              control={control}
              defaultValue=''
              render={({ field }) => (
                <TextField
                  {...field}
                  margin='dense'
                  label='First Name'
                  type='text'
                  fullWidth
                  error={!!errors.first_name}
                  helperText={errors.first_name?.message}
                />
              )}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Controller
              name='last_name'
              control={control}
              defaultValue=''
              render={({ field }) => (
                <TextField
                  {...field}
                  margin='dense'
                  label='Last Name'
                  type='text'
                  fullWidth
                  error={!!errors.last_name}
                  helperText={errors.last_name?.message}
                />
              )}
            />
          </Grid>
          <Controller
            name='role'
            control={control}
            defaultValue='user'
            render={({ field }) => (
              <FormControl fullWidth margin='dense' error={!!errors.role}>
                <InputLabel>Role</InputLabel>
                <Select {...field} label='Role'>
                  <MenuItem value='user'>User</MenuItem>
                  <MenuItem value='superuser'>Super User</MenuItem>
                </Select>
                {errors.role && <FormHelperText>{errors.role?.message}</FormHelperText>}
              </FormControl>
            )}
          />
          <Controller
            name='email'
            control={control}
            defaultValue=''
            render={({ field }) => (
              <TextField
                {...field}
                margin='dense'
                label='Email address'
                type='email'
                fullWidth
                error={!!errors.email}
                helperText={errors.email?.message}
              />
            )}
          />
          <Button
            onClick={() => setEditPassword(!editPassword)}
            onMouseDown={(e) => e.preventDefault()}
          >
            {editPassword ? 'Hide Password' : 'Edit Password'}
          </Button>
          {editPassword && (
            <Controller
              name='password'
              control={control}
              defaultValue=''
              render={({ field }) => (
                <PasswordField
                  {...field}
                  label='Password'
                  error={errors.password}
                  helperText={errors.password?.message}
                />
              )}
            />
          )}
        </Grid>
      </DialogContent>
      <DialogActions sx={{ padding: '1rem' }}>
        <Button onClick={handleCloseAndReset} color='neutral' variant='outlined'>
          Cancel
        </Button>
        <Button type='submit' color='primary' variant='contained'>
          Submit
        </Button>
      </DialogActions>
    </PersistentDialog>
  );
};
