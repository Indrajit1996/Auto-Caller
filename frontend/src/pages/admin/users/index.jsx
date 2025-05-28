import { useCallback, useMemo, useState } from 'react';

import AddIcon from '@mui/icons-material/Add';
import DownloadIcon from '@mui/icons-material/Download';
import { Button, Chip, Stack } from '@mui/material';
import { Link as RouterLink } from 'react-router';

import usersApi from '@/api/users';
import { ApproveUserDialog } from '@/components/Dialogs/ApproveUserDialog';
import { CreateUserDialog } from '@/components/Dialogs/CreateUserDialog';
import { DeactivatedUserDialog } from '@/components/Dialogs/DeactivateUserDialog';
import { EditUserDialog } from '@/components/Dialogs/EditUserDialog';
import { RestoreUserDialog } from '@/components/Dialogs/RestoreUserDialog';
import { PageHeader } from '@/components/PageHeader';
import ServerSideDataTable from '@/components/ServerSideDataTable';
import { ROUTES } from '@/constants/routeConstants';
import { formatDate } from '@/utils/common';

const Users = () => {
  const [data, setData] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [userId, setUserId] = useState(null);
  const [isEditUserOpen, setIsEditUserOpen] = useState(false);
  const [isCreateUserOpen, setIsCreateUserOpen] = useState(false);
  const [isDeleteUserOpen, setIsDeleteUserOpen] = useState(false);
  const [isRestoreDialogOpen, setIsRestoreDialogOpen] = useState(false);
  const [isApproveDialogOpen, setIsApproveDialogOpen] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [dataUpdatedAt, setDataUpdatedAt] = useState(new Date());

  const refreshUsers = useCallback(() => {
    setDataUpdatedAt(new Date());
  }, []);

  // Define filter options
  const userStatusFilterOptions = [
    { value: 'active', label: 'Active' },
    { value: 'pending_admin_approval', label: 'Pending Admin Approvals' },
    { value: 'deactivated', label: 'Deactivated' },
  ];

  const filters = [
    {
      id: 'status',
      label: 'User Status',
      type: 'chips',
      options: userStatusFilterOptions,
    },
    {
      id: 'role',
      label: 'Role',
      type: 'select',
      options: [
        { value: 'user', label: 'User' },
        { value: 'superuser', label: 'Super User' },
      ],
    },
    {
      id: 'created_at',
      label: 'Created At',
      type: 'date',
    },
  ];

  const defaultFilters = {
    status: 'active',
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
            sx={{ textTransform: 'none' }}
            component={RouterLink}
            to={`${ROUTES.ADMIN.USERS_DETAIL.replace(':userId', row.id)}`}
          >{`${row.first_name} ${row.last_name}`}</Button>
        ),
      },
      {
        id: 'role',
        label: 'Role',
        sortable: false,
        render: (row) => (
          <Chip
            label={row.is_superuser ? 'Super User' : 'User'}
            color={row.is_superuser ? 'primary' : 'default'}
            size='small'
          />
        ),
      },
      { id: 'email', label: 'Email', sortable: true },
      {
        id: 'created_at',
        label: 'Created At',
        sortable: true,
        render: (row) => formatDate(row.created_at),
      },
      {
        id: 'status',
        label: 'Status',
        hidden: true,
        render: (row) => {
          switch (row.status) {
            case 'active':
              return <Chip label='Active' color='primary' size='small' />;
            case 'pending_admin_approval':
              return <Chip label='Pending Admin Approval' color='warning' size='small' />;
            case 'pending_email_verification':
              return <Chip label='Pending Email Verification' color='neutral' size='small' />;
            case 'deactivated':
              return <Chip label='Deactivated' color='error' size='small' />;
            default:
              return <Chip label='Unknown' color='neutral' size='small' />;
          }
        },
      },
      {
        id: 'actions',
        label: 'Actions',
        sortable: false,
        render: (row) => rowActions(row),
      },
    ],
    []
  );

  const fetchData = useCallback(
    async (
      page = 0,
      rowsPerPage = 10,
      orderBy = 'created_at',
      order = 'desc',
      search = '',
      filters = {}
    ) => {
      try {
        setLoading(true);
        const requestBody = {
          limit: rowsPerPage,
          offset: page * rowsPerPage,
          search,
          filters,
          order,
          order_by: orderBy,
        };

        const response = await usersApi.getUsersDataTable(requestBody);

        setData(response.data.data || []);
        setTotalCount(response.data.count || 0);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const handleRestoreClick = (id) => {
    setUserId(id);
    setIsRestoreDialogOpen(true);
  };

  const openApproveDialog = (id) => {
    setUserId(id);
    setIsApproveDialogOpen(true);
  };

  const handleDownload = async () => {
    try {
      setIsDownloading(true);
      const response = await usersApi.exportUserData();

      // Create blob from response data
      const blob = new Blob([response.data], {
        type: response.headers['content-type'],
      });

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');

      // Set filename
      const filename = `users.csv`;

      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();

      // Cleanup
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading users:', error);
    } finally {
      setIsDownloading(false);
    }
  };

  const pageHeaderActions = [
    {
      label: isDownloading ? 'Downloading...' : 'Export to CSV',
      icon: DownloadIcon,
      onClick: handleDownload,
      disabled: isDownloading,
      variant: 'outlined',
    },
    {
      label: 'Create User',
      icon: AddIcon,
      onClick: () => setIsCreateUserOpen(true),
      variant: 'contained',
    },
  ];

  const EditUserButton = ({ userId }) => (
    <Button
      size='small'
      variant='outlined'
      onClick={() => {
        setIsEditUserOpen(true);
        setUserId(userId);
      }}
    >
      Edit
    </Button>
  );

  const rowActions = (row) => {
    switch (row.status) {
      case 'active':
        return (
          <Stack direction='row' spacing={1}>
            <EditUserButton userId={row.id} />
            {!row.is_superuser && (
              <Button
                size='small'
                variant='outlined'
                color='error'
                onClick={() => {
                  setIsDeleteUserOpen(true);
                  setUserId(row.id);
                }}
              >
                Deactivate
              </Button>
            )}
          </Stack>
        );

      case 'deactivated':
        return (
          <Stack direction='row' spacing={1}>
            <Button size='small' variant='outlined' onClick={() => handleRestoreClick(row.id)}>
              Restore
            </Button>
          </Stack>
        );

      case 'pending_admin_approval':
        return (
          <Stack direction='row' spacing={1}>
            <Button
              size='small'
              variant='outlined'
              color='success'
              onClick={() => openApproveDialog(row.id)}
            >
              Approve
            </Button>
            <Button
              size='small'
              variant='outlined'
              color='error'
              onClick={() => {
                setIsDeleteUserOpen(true);
                setUserId(row.id);
              }}
            >
              Reject
            </Button>
          </Stack>
        );

      case 'pending_email_verification':
        return (
          <Stack direction='row' spacing={1}>
            <Button
              size='small'
              variant='outlined'
              color='success'
              onClick={() => openApproveDialog(row.id)}
            >
              Approve
            </Button>
          </Stack>
        );

      default:
        return (
          <Stack direction='row' spacing={1}>
            <EditUserButton userId={row.id} />
          </Stack>
        );
    }
  };

  return (
    <>
      <PageHeader title='Users' subtitle='Manage users and admins' actions={pageHeaderActions} />

      <ServerSideDataTable
        data={data}
        columns={columns}
        totalCount={totalCount}
        defaultSort={{ order: 'desc', orderBy: 'created_at' }}
        defaultRowsPerPage={10}
        loading={loading}
        filters={filters}
        defaultFilters={defaultFilters}
        fetchData={fetchData}
        refreshDataTrigger={dataUpdatedAt}
      />

      <CreateUserDialog
        open={isCreateUserOpen}
        handleClose={() => {
          setIsCreateUserOpen(false);
        }}
        onSuccess={refreshUsers}
      />

      <EditUserDialog
        id={userId}
        open={isEditUserOpen}
        onClose={() => {
          setIsEditUserOpen(false);
        }}
        onSuccess={refreshUsers}
      />

      <DeactivatedUserDialog
        id={userId}
        open={isDeleteUserOpen}
        onClose={() => {
          setIsDeleteUserOpen(false);
        }}
        onSuccess={refreshUsers}
      />

      <RestoreUserDialog
        id={userId}
        open={isRestoreDialogOpen}
        onClose={() => {
          setIsRestoreDialogOpen(false);
        }}
        onSuccess={refreshUsers}
      />

      <ApproveUserDialog
        id={userId}
        open={isApproveDialogOpen}
        onClose={() => {
          setIsApproveDialogOpen(false);
        }}
        onSuccess={refreshUsers}
      />
    </>
  );
};

export default Users;
