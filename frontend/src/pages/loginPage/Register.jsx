import { useEffect, useState } from 'react';
import { yupResolver } from '@hookform/resolvers/yup';
import { Button, Divider, Grid2 as Grid, TextField, Typography } from '@mui/material';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router';
import { Link as RouterLink } from 'react-router';
import { useSearchParams } from 'react-router';
import * as yup from 'yup';

import authApi from '@/api/auth';
import invitationsApi from '@/api/invitations';
import PasswordField from '@/components/PasswordField';
import { ROUTES } from '@/constants/routeConstants';
import { useAuth } from '@/hooks';
import { useSnackbar } from '@/hooks/useSnackbar';
import {
  confirmPasswordSchema,
  emailSchema,
  firstNameSchema,
  lastNameSchema,
  passwordSchema,
} from '@/utils/validation';

const registerSchema = yup.object().shape({
  email: emailSchema,
  password: passwordSchema,
  confirmPassword: confirmPasswordSchema,
  first_name: firstNameSchema,
  last_name: lastNameSchema,
});

const Register = () => {
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    setValue,
  } = useForm({
    resolver: yupResolver(registerSchema),
    mode: 'onChange',
  });
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [emailDisabled, setEmailDisabled] = useState(false);

  const { showSuccess, showError } = useSnackbar();
  const navigate = useNavigate();
  const { setPendingEmailVerificationEmail } = useAuth();

  useEffect(() => {
    const fetchInvitation = async () => {
      if (token) {
        try {
          const response = await invitationsApi.getInvitationByToken(token);
          if (response.data.email) {
            setValue('email', response.data.email);
            setEmailDisabled(true);
          }
        } catch (error) {
          console.error('Error fetching invitation:', error);
          showError('Invalid or expired invitation token');
          navigate(ROUTES.AUTH.REGISTER);
        }
      }
    };

    fetchInvitation();
  }, [token, navigate, setValue, showError]);

  const onSubmit = async (data) => {
    if (isValid) {
      if (token) {
        data.invitation_token = token;
      }
      try {
        const res = await authApi.registerUser(data);
        if ([200, 201].includes(res.status)) {
          if (res.data?.status === 'PENDING_EMAIL_VERIFICATION') {
            try {
              setPendingEmailVerificationEmail(data.email);
            } catch (error) {
              console.error('Failed to set pending verification email:', error);
            }
            showSuccess(
              res.data?.message || 'Account created successfully. Please verify your email.'
            );
            navigate(ROUTES.AUTH.VERIFY_EMAIL);
            return;
          }
          if (res.data?.status === 'PENDING_ADMIN_APPROVAL') {
            showSuccess(
              res.data?.message || 'Account created successfully. Please wait for admin approval.'
            );
            navigate(ROUTES.AUTH.LOGIN);
            return;
          }
          navigate(ROUTES.AUTH.LOGIN);
          showSuccess(res.data?.message || 'Account created successfully');
        }
      } catch (error) {
        showError(error.response?.data?.detail?.message || 'Failed to create account');
      }
    } else {
      showError('Please fill in all required fields');
    }
  };

  return (
    <Grid
      container
      justifyContent="center"
      alignItems="center"
      // sx={{
      //   padding: 2,
      // }}
    >
      <Grid
        item
        sx={{
          width: '100%',
          maxWidth: 500,
          backgroundColor: 'white',
          // padding: 4,
          borderRadius: 2,
          // boxShadow: 3,
          overflowY: 'auto', // Optional: scroll if content overflows
        }}
      >
        <Typography component="h1" variant="h5" align="center" sx={{ mb: 4 }}>
          Create a new account
        </Typography>
        <Grid container spacing={2} component="form" noValidate onSubmit={handleSubmit(onSubmit)}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              required
              fullWidth
              id="first_name"
              label="First Name"
              autoComplete="given-name"
              autoFocus
              error={!!errors.first_name}
              helperText={errors.first_name?.message}
              {...register('first_name')}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <TextField
              required
              fullWidth
              id="last_name"
              label="Last Name"
              autoComplete="family-name"
              error={!!errors.last_name}
              helperText={errors.last_name?.message}
              {...register('last_name')}
            />
          </Grid>
          <TextField
            required
            fullWidth
            id="email"
            label="Email Address"
            autoComplete="email"
            error={!!errors.email}
            helperText={errors.email?.message}
            disabled={emailDisabled}
            slotProps={{
              inputLabel: {
                shrink: emailDisabled || undefined,
              },
            }}
            placeholder="user@gmail.com"
            {...register('email')}
          />
          <PasswordField
            required
            fullWidth
            label="Password"
            error={!!errors.password}
            helperText={errors.password?.message}
            {...register('password')}
          />
          <PasswordField
            required
            fullWidth
            label="Confirm Password"
            error={!!errors.confirmPassword}
            helperText={errors.confirmPassword?.message}
            {...register('confirmPassword')}
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            color="primary"
            sx={{ mt: 2 }}
          >
            Register
          </Button>
          <Divider sx={{ my: 2, width: '100%' }} />
          <Button
            variant="outlined"
            color="neutral"
            fullWidth
            component={RouterLink}
            to={ROUTES.AUTH.LOGIN}
          >
            Already have an account? Login
          </Button>
          {/* Back button at the bottom */}
          <Button
            variant="text"
            fullWidth
            onClick={() => navigate(-1)}
            sx={{ mt: 1 }}
          >
            ← Back
          </Button>
        </Grid>
      </Grid>
    </Grid>
  );
};

export default Register;
