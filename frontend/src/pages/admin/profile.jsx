import { yupResolver } from '@hookform/resolvers/yup';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import PersonIcon from '@mui/icons-material/Person';
import {
  Avatar,
  Box,
  Button,
  Chip,
  Divider,
  Grid2 as Grid,
  TextField,
  Typography,
} from '@mui/material';
import { Container } from '@mui/material';
import { Controller, useForm } from 'react-hook-form';
import * as yup from 'yup';

import authApi from '@/api/auth';
import { PageHeader } from '@/components/PageHeader';
import DeactivateSection from '@/components/Profile/DeactivateSection';
import PasswordSection from '@/components/Profile/PasswordSection';
import useAuth from '@/hooks/useAuth';
import { useSnackbar } from '@/hooks/useSnackbar';
import { firstNameSchema, lastNameSchema } from '@/utils/validation';

const schema = yup.object().shape({
  first_name: firstNameSchema,
  last_name: lastNameSchema,
});

const Profile = () => {
  const { user } = useAuth();
  const { showSuccess, showError } = useSnackbar();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: yupResolver(schema),
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
    },
  });

  const { updateUserName } = useAuth();

  const getInitials = () => {
    if (!user?.first_name && !user?.last_name) return '?';
    const firstInitial = user.first_name ? user.first_name[0] : '';
    const lastInitial = user.last_name ? user.last_name[0] : '';
    return (firstInitial + lastInitial).toUpperCase();
  };

  const onSubmit = async (data) => {
    try {
      await authApi.updateProfile({
        first_name: data.first_name,
        last_name: data.last_name,
      });
      showSuccess('Profile updated successfully');
      updateUserName({
        first_name: data.first_name,
        last_name: data.last_name,
      });
    } catch (error) {
      showError(error.response?.data?.message || 'Failed to update settings');
    }
  };

  return (
    <Container maxWidth='lg' sx={{ mt: 4 }}>
      <PageHeader title='Profile' subtitle='Update your profile' actions={[]} />
      <Grid container spacing={2} sx={{ mt: 4 }}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Avatar
            sx={{
              width: 80,
              height: 80,
              bgcolor: 'primary.main',
              fontSize: '2.5rem',
              mb: 2,
            }}
          >
            {getInitials()}
          </Avatar>
          <Typography variant='h6'>
            {user?.first_name} {user?.last_name}
          </Typography>
          <Typography variant='body1' color='text.secondary'>
            {user?.email}
          </Typography>
          <Box sx={{ mt: 2, mb: 1 }}>
            <Chip
              icon={user?.is_superuser ? <AdminPanelSettingsIcon /> : <PersonIcon />}
              label={user?.is_superuser ? 'Superuser' : 'User'}
              color={user?.is_superuser ? 'primary' : 'default'}
              variant='outlined'
              size='small'
            />
          </Box>
        </Grid>

        {/* Right column - Form fields */}
        <Grid container size={{ xs: 12, md: 8 }} spacing={2}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Controller
              name='first_name'
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label='First Name'
                  error={!!errors.first_name}
                  helperText={errors.first_name?.message}
                />
              )}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Controller
              name='last_name'
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label='Last Name'
                  error={!!errors.last_name}
                  helperText={errors.last_name?.message}
                />
              )}
            />
          </Grid>
          <Grid size={12} display='flex' justifyContent='end'>
            <div>
              <Button variant='contained' onClick={handleSubmit(onSubmit)}>
                Save Changes
              </Button>
            </div>
          </Grid>
        </Grid>
      </Grid>

      <Divider sx={{ my: 4 }} />

      <Box sx={{ mb: 4 }}>
        <PasswordSection />

        {!user?.is_superuser && (
          <>
            <Divider sx={{ my: 4 }} />
            <DeactivateSection />
          </>
        )}
      </Box>
    </Container>
  );
};

export default Profile;
