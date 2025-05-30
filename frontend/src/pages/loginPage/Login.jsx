import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Button, Divider, Grid2 as Grid, TextField, Typography } from '@mui/material';

import { useAuth } from '@/hooks';
import { ROUTES } from '@/constants/routeConstants'

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleLogin = async (e) => {
    e.preventDefault();
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    try {
      await login(formData);
      navigate(ROUTES.LOGGED_IN_HOME)
    } catch (error) {
        setMessage(error?.response?.data?.title || 'Login failed');
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
        //   height: '500px',
          backgroundColor: 'white',
          padding: 4,
          borderRadius: 2,
          boxShadow: 3,
          overflowY: 'auto',
        }}
      >
        <Typography component="h1" variant="h5" align="center" sx={{ mb: 4 }}>
          Login
        </Typography>
        <Grid container spacing={2} style={{display: 'block'}} noValidate>
          <Grid xs={12} pb={2}>
            <TextField
                required
                fullWidth
                label="Username"
                value={username}
                onChange={(e) => { 
                    setUsername(e.target.value)
                    setMessage('')
                }}
            />
          </Grid>
          <Grid xs={12} pb={2}>
            <TextField
                required
                fullWidth
                label="Password"
                type="password"
                value={password}
                onChange={(e) => {
                    setPassword(e.target.value)
                    setMessage('')
                }}
            />
          </Grid>
          <Grid xs={12} style={{display: 'flex', justifyContent: 'space-between'}}>
            <Typography
                variant="body2"
                color="primary"
                sx={{ cursor: 'pointer', textAlign: 'right', mt: 1 }}
                onClick={() => navigate('/register')}
            >
                Register
            </Typography>
            <Typography
                variant="body2"
                color="primary"
                sx={{ cursor: 'pointer', textAlign: 'right', mt: 1 }}
                onClick={() => navigate('/forgot-password')}
            >
                Forgot Password?
            </Typography>
          </Grid>

            <Grid xs={12}>
                <Button
                    type="submit"
                    fullWidth
                    variant="contained"
                    color="primary"
                    sx={{ mt: 2 }}
                    onClick={handleLogin}
                >
                    Login
                </Button>
            </Grid>

          {message && (
            <Grid xs={12}>
              <Typography color="error" align="center" sx={{ mt: 2 }}>
                {message}
              </Typography>
            </Grid>
          )}
        </Grid>
      </Grid>
    </Grid>
  );
}

export default Login;
