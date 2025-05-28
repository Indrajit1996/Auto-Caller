// src/ResetPassword.js
import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
    Grid,
    TextField,
    Button,
    Typography,
    Box,
} from '@mui/material';
import { useSnackbar } from '@/hooks/useSnackbar';
import authApi from '@/api/auth';
import { ROUTES } from '@/constants/routeConstants';

export default function ResetPassword() {
    const [searchParams] = useSearchParams();
    // const token = searchParams.get('token') || '';

    // const [newUsername, setNewUsername] = useState('');
    // const [confirmUsername, setConfirmUsername] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [message, setMessage] = useState('');
    const { showSuccess, showError } = useSnackbar();
    const navigate = useNavigate();

    const handleReset = async (e) => {
        e.preventDefault();
        if (newPassword !== confirmPassword) {
            setMessage('Passwords do not match.');
            return;
        }
        try {
            const token = searchParams.get('token');
            if (!token) {
              showError('Reset token is missing');
              return;
            }
            await authApi.resetPassword({
              token,
              new_password: newPassword,
            });
            await showSuccess('Password reset successfully');
            await setTimeout(() => {
                navigate(ROUTES.AUTH.LOGIN);
            }, 2000)
          } catch (error) {
            showError(error?.response?.data?.detail || 'Failed to reset password');
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
                    Set New Username & Password
                </Typography>
                <Box component="form" noValidate>
                    <Grid container spacing={2} style={{ display: 'block' }}>
                        <Grid item xs={12} pb={2}>
                            <TextField
                                required
                                fullWidth
                                label="New Password"
                                type="password"
                                value={newPassword}
                                onChange={(e) => {
                                    setNewPassword(e.target.value); 
                                    setMessage('');
                                }}
                            />
                        </Grid>
                        <Grid item xs={12} pb={2}>
                            <TextField
                                required
                                fullWidth
                                label="Confirm Password"
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => {
                                    setConfirmPassword(e.target.value);
                                    setMessage('');
                                }}
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <Button
                                type="submit"
                                fullWidth
                                variant="contained"
                                color="primary"
                                sx={{ mt: 1 }}
                                onClick={handleReset}
                            >
                                Update
                            </Button>
                        </Grid>
                        {message && (
                            <Grid item xs={12}>
                                <Typography color="error" align="center" sx={{ mt: 2 }}>
                                    {message}
                                </Typography>
                            </Grid>
                        )}
                    </Grid>
                </Box>
            </Grid>
        </Grid>
    );
}
