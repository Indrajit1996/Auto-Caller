import { yupResolver } from '@hookform/resolvers/yup';
import { Button, DialogActions, DialogContent, TextField } from '@mui/material';
import { useForm } from 'react-hook-form';
import * as yup from 'yup';

import groupsApi from '@/api/groups';
import { PersistentDialog } from '@/components/PersistentDialog';
import { useSnackbar } from '@/hooks/useSnackbar';

const schema = yup
  .object({
    name: yup.string().required('Group name is required'),
    description: yup.string(),
  })
  .required();

export const CreateGroupDialog = ({ open, onClose, onGroupAdded }) => {
  const { showSuccess, showError } = useSnackbar();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: yupResolver(schema),
    defaultValues: {
      name: '',
      description: '',
    },
  });

  const onSubmit = async (data) => {
    try {
      await groupsApi.createGroup(data);
      showSuccess('Group created successfully');
      reset();
      onGroupAdded();
      onClose();
    } catch (error) {
      showError(error.response?.data?.message || 'Failed to create group');
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <PersistentDialog
      open={open}
      onClose={handleClose}
      title='Add New Group'
      isForm
      onSubmit={onSubmit}
    >
      <DialogContent dividers>
        <TextField
          {...register('name')}
          label='Group Name'
          fullWidth
          error={!!errors.name}
          helperText={errors.name?.message}
          sx={{ mb: 3 }}
        />
        <TextField
          {...register('description')}
          label='Description'
          fullWidth
          multiline
          rows={4}
          error={!!errors.description}
          helperText={errors.description?.message}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={isSubmitting} color='neutral' variant='outlined'>
          Cancel
        </Button>
        <Button
          type='submit'
          variant='contained'
          disabled={isSubmitting}
          onClick={handleSubmit(onSubmit)}
        >
          {isSubmitting ? 'Creating...' : 'Submit'}
        </Button>
      </DialogActions>
    </PersistentDialog>
  );
};
