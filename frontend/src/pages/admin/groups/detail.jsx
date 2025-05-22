import { useCallback, useEffect, useMemo, useState } from 'react';

import { Add as AddIcon } from '@mui/icons-material';
import ErrorIcon from '@mui/icons-material/Error';
import Box from '@mui/material/Box';
import Breadcrumbs from '@mui/material/Breadcrumbs';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';
import { Link as RouterLink, useParams } from 'react-router';

import groupsApi from '@/api/groups';
import { AddUsersToGroupDialog } from '@/components/Dialogs/AddUsersToGroupDialog';
import { PageHeader } from '@/components/PageHeader';
import ServerSideDataTable from '@/components/ServerSideDataTable';
import { ROUTES } from '@/constants/routeConstants';
import { useSnackbar } from '@/hooks/useSnackbar';

const GroupDetail = () => {
  const { groupId } = useParams();
  const [group, setGroup] = useState({});
  const [groupUsers, setGroupUsers] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [dataUpdatedAt, setDataUpdatedAt] = useState(new Date());
  const [isAddGroupUsersModalOpen, setIsAddGroupUsersModalOpen] = useState(false);

  const { showSuccess, showError } = useSnackbar();

  const refreshGroupUsers = useCallback(() => {
    setDataUpdatedAt(new Date());
  }, []);

  const fetchGroupUsers = useCallback(
    async (page = 0, rowsPerPage = 10, orderBy = 'created_at', order = 'desc', search = '') => {
      try {
        const response = await groupsApi.getGroupUsers({
          offset: page * rowsPerPage,
          limit: rowsPerPage,
          search: search,
          filters: {
            status: 'all',
            role: 'all',
            group: groupId,
          },
          order_by: orderBy,
          order: order.toLowerCase(),
        });

        setGroupUsers({
          data: response.data.data || [],
          total: response.data.count || 0,
        });
      } catch (error) {
        showError(error.response?.data?.detail || 'Failed to fetch group users');
      }
    },
    []
  );

  const handleRemoveUser = async (userId) => {
    try {
      await groupsApi.removeUserFromGroup({ groupId, userId });
      // Refresh the users list after removal
      showSuccess('User removed from group');
      refreshGroupUsers();
    } catch (error) {
      showError(error.response?.data?.detail || 'Failed to remove user from group');
    }
  };

  const columns = useMemo(
    () => [
      {
        id: 'first_name',
        label: 'Name',
        sortable: true,
        render: (row) => (
          <Button
            size='small'
            variant='text'
            component={RouterLink}
            to={`${ROUTES.ADMIN.USERS_DETAIL.replace(':userId', row.id)}`}
            sx={{ textTransform: 'none' }}
          >{`${row.first_name} ${row.last_name}`}</Button>
        ),
      },
      { id: 'email', label: 'Email', sortable: true },
      {
        id: 'actions',
        label: 'Actions',
        sortable: false,
        render: (row) => (
          <Button
            variant='outlined'
            size='small'
            color='error'
            onClick={() => handleRemoveUser(row.id)}
          >
            Remove
          </Button>
        ),
      },
    ],
    []
  );

  useEffect(() => {
    const fetchGroup = async () => {
      try {
        setLoading(true);
        setError(false);
        const response = await groupsApi.getGroup(groupId);
        if (response.data) {
          setGroup(response.data);
        } else {
          setError(true);
          showError('Group data not found');
        }
      } catch (error) {
        console.error('Error fetching group:', error);
        setError(true);
        showError(error.response?.data?.detail || 'Failed to fetch group');
      } finally {
        setLoading(false);
      }
    };
    fetchGroup();
  }, []);

  const pageHeaderActions = [
    {
      label: 'Add Users',
      icon: AddIcon,
      onClick: () => setIsAddGroupUsersModalOpen(true),
      variant: 'contained',
      disabled: loading || error,
    },
  ];

  return (
    <>
      <Breadcrumbs aria-label='breadcrumb' sx={{ mb: 2 }}>
        <Link component={RouterLink} to={ROUTES.LOGGED_IN_HOME} color='inherit' underline='hover'>
          Dashboard
        </Link>
        <Link component={RouterLink} to={ROUTES.ADMIN.GROUPS} color='inherit' underline='hover'>
          Groups
        </Link>
        <Typography color='text.primary'>{group?.name || 'Group Users'}</Typography>
      </Breadcrumbs>

      <PageHeader
        title={group?.name || 'Group Users'}
        subtitle={group?.description}
        actions={pageHeaderActions}
      />

      {loading ? (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant='body1' align='center' py={4}>
              Loading group details...
            </Typography>
          </CardContent>
        </Card>
      ) : error ? (
        <Box
          sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '30vh' }}
        >
          <ErrorIcon color='error' sx={{ fontSize: 40, mr: 1 }} />
          <Typography variant='body1' color='error' align='center'>
            Error loading group details. Please try again later.
          </Typography>
        </Box>
      ) : (
        <ServerSideDataTable
          data={groupUsers?.data || []}
          columns={columns}
          totalCount={groupUsers?.total || 0}
          defaultSort={{ order: 'desc', orderBy: 'created_at' }}
          defaultRowsPerPage={10}
          loading={loading}
          filters={[]}
          defaultFilters={{}}
          fetchData={fetchGroupUsers}
          refreshDataTrigger={dataUpdatedAt}
        />
      )}

      <AddUsersToGroupDialog
        open={isAddGroupUsersModalOpen}
        onClose={() => setIsAddGroupUsersModalOpen(false)}
        groupId={groupId}
        onUsersAdded={refreshGroupUsers}
      />
    </>
  );
};

export default GroupDetail;
