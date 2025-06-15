import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Grid2 as Grid, TextField, Typography, Box } from '@mui/material';
import { useAuth } from '@/hooks';
import { ROUTES } from '@/constants/routeConstants'
import PasswordField from '@/components/PasswordField';

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
      navigate(ROUTES.LOGGED_IN_HOME);
    } catch (error) {
      setMessage(error?.message?.title + '. ' + error?.message?.message);
    }
  };

  return (
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
          sx={{
            '& .MuiInputBase-input': {
              padding: '15px',
              fontSize: '1.1rem'
            },
            '& .MuiInputLabel-root': {
              fontSize: '1.1rem'
            }
          }}
        />
      </Grid>
      <Grid xs={12} pb={2}>
        <PasswordField
          required
          fullWidth
          label="Password"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value)
            setMessage('')
          }}
          sx={{
            '& .MuiInputBase-input': {
              padding: '15px',
              fontSize: '1.1rem'
            },
            '& .MuiInputLabel-root': {
              fontSize: '1.1rem'
            }
          }}
        />
      </Grid>
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'space-between',
          width: '100%',
          mt: 1,
          px: 0
        }}
      >
        <Typography
          variant="body2"
          color="primary"
          sx={{ 
            cursor: 'pointer',
            flex: '0 0 auto',
            ml: -6
          }}
          onClick={() => navigate('/register')}
        >
          Register
        </Typography>
        <Typography
          variant="body2"
          color="primary"
          sx={{ 
            cursor: 'pointer',
            flex: '0 0 auto',
            mr: -6
          }}
          onClick={() => navigate('/forgot-password')}
        >
          Forgot Password?
        </Typography>
      </Box>

      <Grid xs={12}>
        <Button
          type="submit"
          fullWidth
          variant="contained"
          color="primary"
          sx={{ mt: 3 }}
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
  );
}

export default Login;
