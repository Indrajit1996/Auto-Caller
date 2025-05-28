import { Button, DialogActions, DialogContent, DialogContentText } from '@mui/material';

import invitationsApi from '@/api/invitations';
import { PersistentDialog } from '@/components/PersistentDialog';
import { useSnackbar } from '@/hooks/useSnackbar';

export const DeactivateInvitationDialog = ({ id, open, onClose, onSuccess }) => {
  const { showSuccess } = useSnackbar();

  const deactivateInvitation = async () => {
    if (id) {
      try {
        await invitationsApi.deactivateInvitation(id);
        showSuccess('Invitation deactivated successfully');
        onSuccess?.();
        onClose();
      } catch (error) {
        console.error('Error deactivating invitation:', error);
      }
    }
  };

  return (
    <PersistentDialog open={open} onClose={onClose} title='Deactivate Invitation'>
      <DialogContent dividers>
        <DialogContentText>Are you sure you want to deactivate this invitation?</DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} variant='outlined' color='neutral'>
          Cancel
        </Button>
        <Button onClick={deactivateInvitation} variant='contained' color='primary'>
          Deactivate
        </Button>
      </DialogActions>
    </PersistentDialog>
  );
};
