import { Button, DialogActions, DialogContent, DialogContentText } from '@mui/material';

import groupsApi from '@/api/groups';
import { PersistentDialog } from '@/components/PersistentDialog';
import { useSnackbar } from '@/hooks/useSnackbar';

export const DeleteGroupDialog = ({ open, onClose, groupId, onSuccess }) => {
  const { showSuccess, showError } = useSnackbar();

  const handleConfirm = async () => {
    if (groupId) {
      try {
        await groupsApi.deleteGroup({
          group_id: groupId,
        });
        showSuccess('Group deleted successfully');
        onSuccess?.();
      } catch (error) {
        showError(error.response?.data?.message || 'Failed to delete group');
      }
    }
    onClose();
  };

  return (
    <PersistentDialog open={open} onClose={onClose} title='Delete Group' onSubmit={handleConfirm}>
      <DialogContent dividers>
        <DialogContentText id='delete-dialog-description'>
          Are you sure you want to delete this group? This action cannot be undone. All users in
          this group will still remain active
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} variant='outlined' color='neutral'>
          Cancel
        </Button>
        <Button onClick={handleConfirm} variant='contained' color='error'>
          Delete
        </Button>
      </DialogActions>
    </PersistentDialog>
  );
};
