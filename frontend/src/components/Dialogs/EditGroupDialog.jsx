import { useEffect, useState } from 'react';

import { yupResolver } from '@hookform/resolvers/yup';
import {
  Button,
  CircularProgress,
  DialogActions,
  DialogContent,
  Grid2 as Grid,
  TextField,
} from '@mui/material';
import { Controller, useForm } from 'react-hook-form';
import * as yup from 'yup';

import groupsApi from '@/api/groups';
import { PersistentDialog } from '@/components/PersistentDialog';
import { useSnackbar } from '@/hooks/useSnackbar';

export const EditGroupDialog = ({ open, onClose, id, onSuccess }) => {
  const { showSuccess, showError } = useSnackbar();
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const editGroupSchema = yup.object().shape({
    name: yup
      .string()
      .trim()
      .max(100, 'Group name must not exceed 100 characters')
      .required('Group name is required'),
    description: yup.string().max(500, 'Description must not exceed 500 characters').nullable(),
  });

  const {
    control,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
    setValue,
  } = useForm({
    resolver: yupResolver(editGroupSchema),
    defaultValues: {
      name: '',
      description: '',
    },
  });

  useEffect(() => {
    if (!open || !id) {
      reset();
      return;
    }

    const fetchGroup = async () => {
      setIsLoading(true);
      try {
        const response = await groupsApi.getGroup(id);
        const group = response.data;
        setValue('name', group.name, { shouldDirty: false });
        setValue('description', group.description || '', { shouldDirty: false });
      } catch (error) {
        console.error('Failed to fetch group:', error);
        showError(error.response?.data?.detail || 'Failed to load group details');
        onClose();
      } finally {
        setIsLoading(false);
      }
    };
    fetchGroup();
  }, [open, id, setValue, reset, showError, onClose]);

  const onSubmit = async (data) => {
    if (!isDirty) {
      onClose();
      return;
    }

    setIsSubmitting(true);
    const payload = {
      name: data.name.trim(),
      description: data.description?.trim() || null,
    };

    try {
      await groupsApi.updateGroup(id, payload);
      onClose();
      showSuccess('Group updated successfully');
      onSuccess?.();
    } catch (error) {
      console.error('Failed to update group:', error);
      showError(error.response?.data?.detail || 'Failed to update group');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCloseAndReset = () => {
    if (isSubmitting || isLoading) return;
    reset();
    onClose();
  };

  return (
    <PersistentDialog
      open={open}
      onClose={handleCloseAndReset}
      onSubmit={handleSubmit(onSubmit)}
      title='Edit Group'
      isForm
      disabled={isLoading || isSubmitting}
    >
      <DialogContent dividers>
        {isLoading ? (
          <Grid container justifyContent='center' padding={2}>
            <CircularProgress size={40} />
          </Grid>
        ) : (
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <Controller
                name='name'
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    margin='dense'
                    label='Group Name'
                    type='text'
                    fullWidth
                    error={!!errors.name}
                    helperText={errors.name?.message}
                    disabled={isSubmitting}
                    required
                  />
                )}
              />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <Controller
                name='description'
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    margin='dense'
                    label='Description'
                    type='text'
                    fullWidth
                    multiline
                    rows={4}
                    error={!!errors.description}
                    helperText={errors.description?.message}
                    disabled={isSubmitting}
                  />
                )}
              />
            </Grid>
          </Grid>
        )}
      </DialogContent>
      <DialogActions sx={{ padding: '1rem' }}>
        <Button
          onClick={handleCloseAndReset}
          color='neutral'
          variant='outlined'
          disabled={isSubmitting || isLoading}
        >
          Cancel
        </Button>
        <Button
          type='submit'
          color='primary'
          variant='contained'
          disabled={isSubmitting || isLoading || (!isDirty && open)}
          startIcon={isSubmitting && <CircularProgress size={20} color='inherit' />}
        >
          {isSubmitting ? 'Saving...' : 'Save'}
        </Button>
      </DialogActions>
    </PersistentDialog>
  );
};
