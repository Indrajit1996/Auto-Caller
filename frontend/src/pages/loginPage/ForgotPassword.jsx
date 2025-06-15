// src/ForgotPassword.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Grid,
  Typography,
  TextField,
  Button,
} from '@mui/material';
import { useSnackbar } from '@/hooks/useSnackbar';
import authApi from '@/api/auth';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();
  const { showSuccess, showError } = useSnackbar();

  const handleReset = async (e, val) => {
    e.preventDefault();
    // const host = window.location.hostname;
    try {
      const response = await authApi.passwordRecovery(email); 
      showSuccess(response.data.message);
    } catch (error) {
      if (error.response) {
        if (error.response.status === 404) {
          showError(error.response.data.detail);
        } else if (error.response.status === 422) {
          showError('Invalid email format');
        } else {
          showError(error.response.data.detail || 'An error occurred');
        }
      } else {
        showError('Failed to connect to the server. Please try again');
      }
    }
  };

  return (
    <Grid
      container
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
      sx={{
        background: 'linear-gradient(to right, #e0eafc, #cfdef3)',
        padding: 2,
      }}
    >
      <Grid
        item
        sx={{
          width: '500px',
          backgroundColor: 'white',
          padding: 4,
          borderRadius: 2,
          boxShadow: 3,
        }}
      >
        <Typography component="h1" variant="h5" align="center" sx={{ mb: 4 }}>
          Forgot Password
        </Typography>

        <Grid container spacing={2} style={{ display: 'block' }}>
          <Grid item xs={12} pb={2}>
            <TextField
              required
              fullWidth
              type="email"
              label="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </Grid>

          {message && (
            <Grid item xs={12}>
              <Typography color="error" align="center" sx={{ mb: 2 }}>
                {message}
              </Typography>
            </Grid>
          )}

          <Grid item xs={12}>
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              sx={{ mt: 2 }}
              onClick={handleReset}
            >
              Send Reset Link
            </Button>
          </Grid>

          <Grid item xs={12}>
            <Button
              fullWidth
              variant="text"
              color="secondary"
              onClick={() => navigate('/')}
              sx={{ mt: 1 }}
            >
              Back to Login
            </Button>
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  );
}
