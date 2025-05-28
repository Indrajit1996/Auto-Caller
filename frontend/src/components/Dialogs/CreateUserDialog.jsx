import { useState } from 'react';

import { yupResolver } from '@hookform/resolvers/yup';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import {
  Button,
  DialogActions,
  DialogContent,
  FormControl,
  FormHelperText,
  Grid2 as Grid,
  IconButton,
  InputAdornment,
  InputLabel,
  MenuItem,
  Select,
  TextField,
} from '@mui/material';
import { Controller, useForm } from 'react-hook-form';
import * as yup from 'yup';

import usersApi from '@/api/users';
import { PersistentDialog } from '@/components/PersistentDialog';
import { useSnackbar } from '@/hooks/useSnackbar';
import { emailSchema, firstNameSchema, lastNameSchema, passwordSchema } from '@/utils/validation';

const createUserSchema = yup.object().shape({
  email: emailSchema,
  password: passwordSchema,
  first_name: firstNameSchema,
  last_name: lastNameSchema,
  role: yup.string().oneOf(['user', 'superuser'], 'Invalid role').required('Role is required'),
});

const defaultValues = {
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  role: 'user',
};

export const CreateUserDialog = ({ open, handleClose, onSuccess }) => {
  const {
    control,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm({
    resolver: yupResolver(createUserSchema),
    defaultValues,
  });

  const [showPassword, setShowPassword] = useState(false);
  const { showSuccess, showError } = useSnackbar();

  const onSubmit = async (data) => {
    try {
      await usersApi.addUser({
        first_name: data.first_name,
        last_name: data.last_name,
        is_superuser: data.role === 'superuser', // Convert string role to boolean
        email: data.email,
        password: data.password,
      });
      handleCloseAndReset();
      showSuccess('User created successfully');
      onSuccess();
    } catch (error) {
      showError(error?.response?.data?.detail?.message);
      console.error(error);
    }
  };

  const handleCloseAndReset = () => {
    reset(defaultValues);
    handleClose();
  };

  return (
    <PersistentDialog
      open={open}
      onClose={handleCloseAndReset}
      title='Create New User'
      isForm
      onSubmit={handleSubmit(onSubmit)}
    >
      <DialogContent dividers>
        <Grid container spacing={1}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Controller
              name='first_name'
              control={control}
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
            render={({ field }) => (
              <TextField
                {...field}
                margin='dense'
                label='Email address'
                fullWidth
                error={!!errors.email}
                helperText={errors.email?.message}
              />
            )}
          />
          <Controller
            name='password'
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                margin='dense'
                label='Password'
                type={showPassword ? 'text' : 'password'}
                fullWidth
                error={!!errors.password}
                helperText={errors.password?.message}
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position='end'>
                        <IconButton
                          aria-label='toggle password visibility'
                          onClick={() => setShowPassword(!showPassword)}
                          onMouseDown={(e) => e.preventDefault()}
                          edge='end'
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  },
                }}
              />
            )}
          />
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
