import { Button, DialogActions, DialogContent, DialogContentText } from '@mui/material';

import usersApi from '@/api/users';
import { PersistentDialog } from '@/components/PersistentDialog';
import { useSnackbar } from '@/hooks/useSnackbar';

export const RestoreUserDialog = ({ id, open, onClose, onSuccess }) => {
  const { showSuccess } = useSnackbar();

  const handleConfirm = async () => {
    if (id) {
      try {
        await usersApi.updateStatus(id, 'active');
        showSuccess('User restored successfully');
        onSuccess?.();
      } catch (error) {
        console.error('Error restoring user:', error);
      }
    }
    onClose();
  };

  return (
    <PersistentDialog open={open} onClose={onClose} title='Restore User'>
      <DialogContent dividers>
        <DialogContentText id='restore-dialog-description'>
          Are you sure you want to restore this user?
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} variant='outlined' color='neutral'>
          Cancel
        </Button>
        <Button onClick={handleConfirm} variant='contained' color='primary'>
          Restore
        </Button>
      </DialogActions>
    </PersistentDialog>
  );
};
