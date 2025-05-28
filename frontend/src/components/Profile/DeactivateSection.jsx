import { useState } from 'react';

import { DeleteForever as DeleteIcon } from '@mui/icons-material';
import { Box, Button, Typography } from '@mui/material';
import { red } from '@mui/material/colors';

import authApi from '@/api/auth';
import useAuth from '@/hooks/useAuth';
import { useSnackbar } from '@/hooks/useSnackbar';

const DeactivateSection = () => {
  const [showDeactivateConfirm, setShowDeactivateConfirm] = useState(false);
  const { showSuccess, showError } = useSnackbar();
  const { logout } = useAuth();

  const handleDeactivateAccount = async () => {
    try {
      await authApi.deactivateAccount();
      showSuccess('Account deactivated successfully');
      logout();
    } catch (error) {
      showError(error.response?.data?.detail || 'Failed to deactivate account');
    }
    setShowDeactivateConfirm(false);
  };

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DeleteIcon sx={{ color: red[500] }} />
          <Typography variant='h6' sx={{ color: red[500] }}>
            Deactivate Account
          </Typography>
        </Box>
        <Button
          variant='outlined'
          color='error'
          onClick={() => setShowDeactivateConfirm(!showDeactivateConfirm)}
        >
          Deactivate
        </Button>
      </Box>

      {showDeactivateConfirm && (
        <Box sx={{ mt: 2 }}>
          <Typography color='error' sx={{ mb: 2 }}>
            Are you sure you want to deactivate your account? This action cannot be undone.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button variant='contained' color='error' onClick={handleDeactivateAccount}>
              Yes, Deactivate
            </Button>
            <Button
              variant='outlined'
              onClick={() => setShowDeactivateConfirm(false)}
              color='neutral'
            >
              Cancel
            </Button>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default DeactivateSection;
