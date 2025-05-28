import { useState } from 'react';

import { yupResolver } from '@hookform/resolvers/yup';
import CheckIcon from '@mui/icons-material/Check';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import {
  Box,
  Button,
  Chip,
  DialogActions,
  DialogContent,
  Grid2 as Grid,
  IconButton,
  InputAdornment,
  Tab,
  Tabs,
  TextField,
  Tooltip,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import dayjs from 'dayjs';
import { Controller, useForm } from 'react-hook-form';
import * as yup from 'yup';

import invitationsApi from '@/api/invitations';
import { PersistentDialog } from '@/components/PersistentDialog';
import { useSnackbar } from '@/hooks/useSnackbar';
import { validateEmail } from '@/utils/validateEmail';
import { optinalEmailSchema } from '@/utils/validation';

const inviteUserSchema = yup.object().shape({
  emails: yup.array().when('type', {
    is: 'email',
    then: () => yup.array().of(optinalEmailSchema).min(1, 'At least one email is required'),
    otherwise: () => yup.array().nullable(),
  }),
  type: yup.string().oneOf(['email', 'link']).required(),
  user_expiry_date: yup.date().nullable().min(new Date()),
});

export const InviteUserDialog = ({ open, handleClose, onSuccess }) => {
  const [tabValue, setTabValue] = useState(0);
  const [emails, setEmails] = useState([]);
  const [currentEmail, setCurrentEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [invitationLink, setInvitationLink] = useState('');
  const [copySuccess, setCopySuccess] = useState(false);
  const [generated, setGenerated] = useState(false);

  const { showSuccess, showInfo, showError } = useSnackbar();

  const {
    control,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
  } = useForm({
    resolver: yupResolver(inviteUserSchema),
    defaultValues: {
      type: 'email',
      emails: [],
      user_expiry_date: null,
    },
  });

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setValue('type', newValue === 0 ? 'email' : 'link');
    setValue('email', '');
  };

  const handleEmailKeyPress = (event) => {
    if (event.key === 'Enter' && currentEmail) {
      event.preventDefault();
      const { isValid, error } = validateEmail(currentEmail);

      if (isValid) {
        const newEmails = [...emails, currentEmail];
        setEmails(newEmails);
        setValue('emails', newEmails);
        setCurrentEmail('');
      } else {
        showError(error);
      }
    }
  };

  const handleDeleteEmail = (emailToDelete) => {
    const newEmails = emails.filter((email) => email !== emailToDelete);
    setEmails(newEmails);
    setValue('emails', newEmails);
  };

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(invitationLink);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy link:', err);
    }
  };

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      const payload = {
        type: data.type,
        emails: data.emails,
        user_expiry_date: data.user_expiry_date,
      };

      if (data.type === 'email') {
        const response = await invitationsApi.createInvitation(payload);
        const existingEmails = response.data?.existing_emails || [];
        const createdInvitations = response.data?.created_invitations || [];
        const invalidEmails = response.data?.invalid_emails || [];

        // Show success message for created invitations
        if (createdInvitations.length) {
          showSuccess(
            `Successfully sent invitations to ${createdInvitations.map((email) => email.email).join(', ')}.`
          );
        }

        if (existingEmails.length) {
          showInfo(
            `Emails already exist as users or pending invitations: ${existingEmails.join(', ')}.`
          );
        }

        if (invalidEmails.length) {
          showError(`Invalid emails: ${invalidEmails.join(', ')}.`);
        }

        handleCloseAndReset();
      } else {
        if (!generated) {
          // Link type invitation
          const response = await invitationsApi.createInvitation(payload);
          setInvitationLink(
            `${window.location.origin}/register?token=${response.data?.created_invitations?.[0]?.token}`
          );
          showSuccess('Invitation link generated successfully');
          setGenerated(true);
        } else {
          // Reset the form
          setInvitationLink('');
          setGenerated(false);
        }
      }

      onSuccess?.();
    } catch (error) {
      console.error('Error creating invitation:', error);
      showError(error.response?.data?.detail || 'Failed to create invitation');
    } finally {
      // wait for 1 second before enabling the submit button
      setTimeout(() => {
        setIsSubmitting(false);
      }, 1000);
    }
  };

  const handleCloseAndReset = () => {
    setEmails([]);
    setCopySuccess(false);
    setInvitationLink('');
    setCurrentEmail('');
    reset();
    setTabValue(0);
    setGenerated(false);
    handleClose();
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <PersistentDialog
        open={open}
        onClose={handleCloseAndReset}
        isForm
        onSubmit={handleSubmit(onSubmit)}
        title='Invite User'
      >
        <DialogContent dividers>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            indicatorColor='primary'
            textColor='primary'
            sx={{ mb: 2, mt: -1 }}
          >
            <Tab label='Email Invitation' />
            <Tab label='Link Invitation' />
          </Tabs>

          <Grid container spacing={1}>
            {tabValue === 0 && (
              <>
                <Box
                  sx={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 1,
                    mb: emails.length ? 1 : 0,
                  }}
                >
                  {emails.map((email, index) => (
                    <Chip
                      key={index}
                      label={email}
                      onDelete={() => handleDeleteEmail(email)}
                      color='primary'
                      variant='outlined'
                      size='small'
                    />
                  ))}
                </Box>
                <Controller
                  name='emails'
                  control={control}
                  render={() => (
                    <TextField
                      value={currentEmail}
                      onChange={(e) => setCurrentEmail(e.target.value)}
                      onKeyDownCapture={handleEmailKeyPress}
                      fullWidth
                      placeholder='Press "Enter" to add email'
                      label='Email Address'
                      type='email'
                      margin='dense'
                      error={!!errors.emails || !!errors.currentEmail}
                      helperText={errors.currentEmail?.message || errors.emails?.message}
                    />
                  )}
                />
              </>
            )}

            <Controller
              name='user_expiry_date'
              control={control}
              render={({ field }) => (
                <DatePicker
                  {...field}
                  label='User Expiry Date'
                  minDate={dayjs()}
                  disabled={generated}
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      margin: 'dense',
                      error: !!errors.user_expiry_date,
                      helperText: errors.user_expiry_date
                        ? errors.user_expiry_date.message
                        : 'User will be deactivated after this date. Leave empty for no expiry',
                    },
                  }}
                />
              )}
            />

            {tabValue === 1 && invitationLink && (
              <TextField
                fullWidth
                value={invitationLink}
                label='Invitation Link'
                variant='outlined'
                margin='dense'
                slotProps={{
                  input: {
                    readOnly: true,
                    endAdornment: (
                      <InputAdornment position='end'>
                        <Tooltip title={copySuccess ? 'Copied!' : 'Copy to clipboard'}>
                          <IconButton onClick={handleCopyLink}>
                            {copySuccess ? <CheckIcon /> : <ContentCopyIcon />}
                          </IconButton>
                        </Tooltip>
                      </InputAdornment>
                    ),
                  },
                }}
              />
            )}
          </Grid>
        </DialogContent>
        <DialogActions sx={{ padding: '1rem' }}>
          <Button onClick={handleCloseAndReset} color='neutral' variant='outlined'>
            Cancel
          </Button>
          <Button type='submit' color='primary' variant='contained' disabled={isSubmitting}>
            {isSubmitting
              ? !generated
                ? 'Resetting'
                : 'Generating'
              : tabValue === 0
                ? 'Submit'
                : generated
                  ? 'Reset'
                  : 'Generate Link'}
          </Button>
        </DialogActions>
      </PersistentDialog>
    </LocalizationProvider>
  );
};
