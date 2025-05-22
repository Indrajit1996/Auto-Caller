import { useState } from 'react';

import { Button, DialogActions, DialogContent, DialogContentText } from '@mui/material';

import usersApi from '@/api/users';
import { PersistentDialog } from '@/components/PersistentDialog';
import { useSnackbar } from '@/hooks/useSnackbar';

export const DeactivatedUserDialog = ({ open, onClose, id, onSuccess }) => {
  const [isDeleting, setIsDeleting] = useState(false);
  const { showSuccess, showError } = useSnackbar();

  const handleDeactivateUser = async () => {
    setIsDeleting(true);
    try {
      await usersApi.updateStatus(id, 'deactivated');
      onClose();
      showSuccess('User deactivated successfully');
      onSuccess?.();
    } catch (error) {
      console.error(error);
      showError(error.response?.data?.detail || 'An error occurred');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <PersistentDialog open={open} onClose={onClose} title='Deactivate User'>
      <DialogContent dividers>
        <DialogContentText>
          Are you sure you want to deactivate this user? You can always reactivate them later.
        </DialogContentText>
      </DialogContent>
      <DialogActions sx={{ padding: '1rem' }}>
        <Button
          onClick={onClose}
          variant='outlined'
          size='small'
          disabled={isDeleting}
          color='neutral'
        >
          Cancel
        </Button>
        <Button
          onClick={handleDeactivateUser}
          color='error'
          variant='contained'
          size='small'
          disabled={isDeleting}
        >
          {isDeleting ? 'Deleting...' : 'Deactivate'}
        </Button>
      </DialogActions>
    </PersistentDialog>
  );
};
