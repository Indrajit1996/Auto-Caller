import { useEffect, useState } from 'react';

import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import CheckIcon from '@mui/icons-material/Check';
import EditIcon from '@mui/icons-material/Edit';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';
import PersonIcon from '@mui/icons-material/Person';
import WarningIcon from '@mui/icons-material/Warning';
import {
  Box,
  Breadcrumbs,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  Grid2 as Grid,
  Link,
  Stack,
  Typography,
  alpha,
} from '@mui/material';
import { Link as RouterLink, useNavigate, useParams } from 'react-router';

import usersApi from '@/api/users';
import { EditUserDialog } from '@/components/Dialogs/EditUserDialog';
import { PageHeader } from '@/components/PageHeader';
import { ROUTES } from '@/constants/routeConstants';
import { useSnackbar } from '@/hooks/useSnackbar';
import { formatDate } from '@/utils/common';

const UserDetail = () => {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [isEditUserOpen, setIsEditUserOpen] = useState(false);
  const { showError } = useSnackbar();

  useEffect(() => {
    const fetchUser = async () => {
      try {
        setLoading(true);
        setError(false);
        const response = await usersApi.getUser(userId);
        if (response.data) {
          setUser(response.data);
        } else {
          setError(true);
          showError('User data not found');
        }
      } catch (err) {
        console.error('Error fetching user:', err);
        setError(true);
        showError('Failed to load user details');
      } finally {
        setLoading(false);
      }
    };
    if (userId) {
      fetchUser();
    }
  }, [userId]);

  const handleEditSuccess = async () => {
    try {
      setLoading(true);
      setError(false);
      const response = await usersApi.getUser(userId);
      if (response.data) {
        setUser(response.data);
      } else {
        setError(true);
        showError('User data not found after update');
      }
    } catch (err) {
      console.error('Error refreshing user data:', err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const getStatusChip = (status) => {
    const statusConfig = {
      active: { label: 'Active', color: 'success', icon: <CheckIcon /> },
      pending_admin_approval: {
        label: 'Pending Admin Approval',
        color: 'neutral',
        icon: <WarningIcon />,
      },
      pending_email_verification: {
        label: 'Pending Email Verification',
        color: 'neutral',
        icon: <InfoIcon />,
      },
      deactivated: { label: 'Deactivated', color: 'error', icon: <ErrorIcon /> },
      default: { label: 'Unknown', color: 'default', icon: <ErrorIcon /> },
    };

    const config = statusConfig[status] || statusConfig.default;

    return (
      <Chip
        icon={config.icon}
        label={config.label}
        color={config.color}
        size='small'
        sx={{
          fontWeight: 'medium',
          px: 1,
          border: '1px solid',
          borderColor: (theme) => alpha(theme.palette[config.color].main, 0.2),
        }}
      />
    );
  };

  const handleGroupClick = (groupId) => {
    navigate(`/admin/groups/${groupId}`);
  };

  const pageHeaderActions = [
    {
      label: 'Edit User',
      icon: EditIcon,
      onClick: () => setIsEditUserOpen(true),
      variant: 'contained',
      disabled: loading || !user,
    },
  ];

  const InfoRow = ({ label, value, chip }) => (
    <Grid container spacing={2} sx={{ mb: 2 }}>
      <Grid size={{ xs: 4, md: 2 }}>
        <Typography variant='subtitle2' color='text.secondary'>
          {label}
        </Typography>
      </Grid>
      <Grid size={{ xs: 8, md: 10 }}>
        {chip ? (
          chip
        ) : (
          <Typography
            variant='body1'
            sx={{ fontWeight: value ? 'medium' : 'normal', opacity: value ? 1 : 0.7 }}
          >
            {value || 'Not provided'}
          </Typography>
        )}
      </Grid>
    </Grid>
  );

  return (
    <>
      <Breadcrumbs aria-label='breadcrumb' sx={{ mb: 2 }}>
        <Link component={RouterLink} to={ROUTES.LOGGED_IN_HOME} color='inherit' underline='hover'>
          Dashboard
        </Link>
        <Link component={RouterLink} to={ROUTES.ADMIN.USERS} color='inherit' underline='hover'>
          Users
        </Link>
        <Typography color='text.primary'>
          {user ? `${user.first_name} ${user.last_name}` : 'User Details'}
        </Typography>
      </Breadcrumbs>

      <PageHeader
        title={user ? `${user.first_name} ${user.last_name}` : 'User Details'}
        subtitle={user ? user.email : error ? 'Error loading user' : 'Loading...'}
        actions={pageHeaderActions}
      />

      {loading ? (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant='body1' align='center' py={4}>
              Loading user details...
            </Typography>
          </CardContent>
        </Card>
      ) : error ? (
        <Box
          sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '30vh' }}
        >
          <ErrorIcon color='error' sx={{ fontSize: 40, mr: 1 }} />
          <Typography variant='body1' color='error' align='center'>
            Error loading user details. Please try again later.
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={3} direction='column'>
          <Grid size={{ xs: 12 }}>
            <Card sx={{ mb: 3, height: '100%' }}>
              <CardHeader title='Account Information' />
              <Divider sx={{ mt: 1, mb: 3 }} />
              <CardContent>
                <Box sx={{ px: 1 }}>
                  <InfoRow label='Account Status' chip={getStatusChip(user.status)} />
                  <InfoRow
                    label='Role'
                    chip={
                      <Chip
                        icon={user?.is_superuser ? <AdminPanelSettingsIcon /> : <PersonIcon />}
                        label={user?.is_superuser ? 'Superuser' : 'User'}
                        color={user?.is_superuser ? 'primary' : 'default'}
                        variant='outlined'
                        size='small'
                      />
                    }
                  />
                  {user.groups && user.groups.length > 0 && (
                    <InfoRow
                      label='Groups'
                      chip={
                        <Stack direction='row' gap={1} sx={{ flexWrap: 'wrap' }}>
                          {user.groups.map((group) => (
                            <Chip
                              key={group.id}
                              label={group.name}
                              color='info'
                              size='small'
                              onClick={() => handleGroupClick(group.id)}
                              clickable
                              sx={{
                                fontWeight: 'medium',
                                cursor: 'pointer',
                                '&:hover': {
                                  backgroundColor: (theme) => alpha(theme.palette.info.main, 0.8),
                                },
                              }}
                            />
                          ))}
                        </Stack>
                      }
                    />
                  )}
                  <InfoRow
                    label='Last Login'
                    value={user.last_login ? formatDate(user.last_login) : 'Never'}
                  />
                  <InfoRow label='Created On' value={formatDate(user.created_at)} />
                  <InfoRow label='Last Updated' value={formatDate(user.updated_at)} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {user.invitation && (
            <Grid xs={12} md={6}>
              <Card sx={{ mb: 3, height: '100%' }}>
                <CardHeader title='Invitation Information' />
                <Divider sx={{ mt: 1, mb: 3 }} />
                <CardContent>
                  <Box sx={{ px: 1 }}>
                    <InfoRow
                      label='Invited By'
                      value={
                        user.invitation.created_by_user
                          ? `${user.invitation.created_by_user.first_name} ${user.invitation.created_by_user.last_name} (${user.invitation.created_by_user.email})`
                          : 'Unknown'
                      }
                    />
                    <InfoRow
                      label='Invitation Date'
                      value={formatDate(user.invitation.created_at)}
                    />
                    <InfoRow
                      label='Registration Date'
                      value={user.created_at ? formatDate(user.created_at) : 'Not Registered'}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}

      <EditUserDialog
        id={userId}
        open={isEditUserOpen}
        onClose={() => setIsEditUserOpen(false)}
        onSuccess={handleEditSuccess}
      />
    </>
  );
};

export default UserDetail;
