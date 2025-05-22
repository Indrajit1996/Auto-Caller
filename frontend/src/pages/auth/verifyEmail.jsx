import { useEffect, useState } from 'react';

import { CheckCircle } from '@mui/icons-material';
import {
  Alert,
  AlertTitle,
  Box,
  Button,
  Divider,
  FormControl,
  TextField,
  Typography,
} from '@mui/material';
import { Link } from 'react-router';

import authApi from '@/api/auth';
import { ROUTES } from '@/constants/routeConstants';
import { useSnackbar } from '@/hooks/useSnackbar';
import authStore from '@/store/authStore';

const VerifiedCard = () => {
  return (
    <Box mt={4}>
      <CheckCircle
        fontSize='large'
        color='primary'
        sx={{ display: 'block', margin: '12px auto' }}
      />
      <Typography variant='h5' align='center' sx={{ marginBottom: '1rem' }}>
        Email Verified
      </Typography>
      <Typography variant='body1' align='center'>
        Your email has been verified successfully. You can now log in to your account.
      </Typography>
      <Box mt={8} display='flex' justifyContent='center' maxWidth='300px' mx='auto'>
        <Button
          variant='contained'
          color='primary'
          component={Link}
          to={ROUTES.AUTH.LOGIN}
          fullWidth
        >
          Log In
        </Button>
      </Box>
    </Box>
  );
};

const ResendVerificationCard = ({ userEmail }) => {
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState(userEmail || '');
  const [error, setError] = useState(false);
  const [justSent, setJustSent] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const { showSuccess, showError } = useSnackbar();

  useEffect(() => {
    // If countdown is active, decrease it by 1 every second
    if (countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  // Format countdown to MM:SS
  const formatCountdown = () => {
    const minutes = Math.floor(countdown / 60);
    const seconds = countdown % 60;
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  const sendVerificationEmail = async () => {
    if (!email) {
      setError(true);
      return;
    }

    setLoading(true);
    try {
      const response = await authApi.resendVerificationEmail(email);
      if (response.status === 200) {
        showSuccess('Verification email sent successfully');
        setJustSent(true);
        setCountdown(300); // 5 minutes countdown
      } else {
        showError(response.data?.detail || 'Failed to send verification email');
      }
    } catch (err) {
      console.error(err);
      showError(err.response?.data?.detail || 'Failed to send verification email');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant='h5' align='center' sx={{ marginBottom: '1rem' }}>
        Verify Your Email
      </Typography>

      {justSent ? (
        <Typography variant='body1' align='center'>
          Verification email has been sent to {email}. Please check your inbox and spam folder. It
          may take a few minutes to arrive.
        </Typography>
      ) : (
        <Typography variant='body1' align='center'>
          Thanks for signing up! Before getting started, could you verify your email address by
          clicking on the link we just emailed to you? If you didn&apos;t receive the email, we will
          gladly send you another.
        </Typography>
      )}

      {!justSent && !userEmail && (
        <Box mt={3}>
          <FormControl fullWidth>
            <TextField
              label='Email'
              variant='outlined'
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              error={error}
              helperText={error && 'Email is required'}
            />
          </FormControl>
        </Box>
      )}

      <Button
        fullWidth
        variant='contained'
        color='primary'
        onClick={sendVerificationEmail}
        disabled={loading || countdown > 0}
        sx={{ mt: 4 }}
      >
        {loading
          ? 'Sending...'
          : countdown > 0
            ? `Resend Available in ${formatCountdown()}`
            : justSent
              ? 'Resend Verification Email'
              : 'Resend Verification Link'}
      </Button>

      {justSent && countdown === 0 && (
        <Button
          fullWidth
          variant='text'
          color='primary'
          onClick={() => setJustSent(false)}
          sx={{ mt: 1 }}
        >
          Use a different email
        </Button>
      )}

      <Divider sx={{ my: 4, width: '100%' }} />
      <Button variant='outlined' color='neutral' component={Link} to={ROUTES.AUTH.LOGIN} fullWidth>
        Already Verified? Log In
      </Button>
    </Box>
  );
};

const InvalidTokenAlert = () => {
  return (
    <Alert severity='error' sx={{ width: '100%', my: 4 }}>
      <AlertTitle>Token Invalid or Expired</AlertTitle>
      Please request a new verification link
    </Alert>
  );
};

export const VerifyEmail = () => {
  const [loading, setLoading] = useState(true);
  const [verified, setVerified] = useState(false);
  const [invalidToken, setInvalidToken] = useState(false);
  const [showResendVerification, setShowResendVerification] = useState(false);
  const userEmail = authStore((state) => state.pendingEmailVerificationEmail);

  const verifyEmailToken = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    if (token) {
      try {
        const res = await authApi.verifyEmail(token);
        if (res.status === 200) {
          setVerified(true);
          setInvalidToken(false);
          setShowResendVerification(false);
        } else {
          setVerified(false);
          setInvalidToken(true);
          setShowResendVerification(true);
        }
      } catch (err) {
        console.error(err);
        setInvalidToken(true);
        setShowResendVerification(true);
      } finally {
        setLoading(false);
      }
    } else {
      setLoading(false);
      setShowResendVerification(true);
    }
  };

  useEffect(() => {
    verifyEmailToken();
  }, []);

  return (
    <>
      {verified && <VerifiedCard />}
      {invalidToken && <InvalidTokenAlert />}
      {showResendVerification && <ResendVerificationCard userEmail={userEmail} />}
    </>
  );
};
