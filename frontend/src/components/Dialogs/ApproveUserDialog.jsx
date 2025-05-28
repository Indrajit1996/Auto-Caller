import { Button, DialogActions, DialogContent, DialogContentText } from '@mui/material';

import usersApi from '@/api/users';
import { PersistentDialog } from '@/components/PersistentDialog';
import { useSnackbar } from '@/hooks/useSnackbar';

export const ApproveUserDialog = ({ id, open, onClose, onSuccess }) => {
  const { showSuccess } = useSnackbar();

  const handleConfirm = async () => {
    if (id) {
      try {
        await usersApi.updateStatus(id, 'active');
        showSuccess('User approved successfully');
        onSuccess?.();
      } catch (error) {
        console.error('Error approving user:', error);
      }
    }
    onClose();
  };

  return (
    <PersistentDialog
      open={open}
      onClose={onClose}
      title='Approve User'
      isForm
      onSubmit={handleConfirm}
    >
      <DialogContent dividers>
        <DialogContentText id='restore-dialog-description'>
          Are you sure you want to approve this user?
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} variant='outlined' color='neutral'>
          Cancel
        </Button>
        <Button onClick={handleConfirm} variant='contained' color='primary'>
          Approve
        </Button>
      </DialogActions>
    </PersistentDialog>
  );
};
