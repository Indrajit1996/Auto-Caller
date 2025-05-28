import { useCallback, useMemo, useState } from 'react';

import AddIcon from '@mui/icons-material/Add';
import { Button, Chip, ListItemText, Stack } from '@mui/material';

import invitationsApi from '@/api/invitations';
import { DeactivateInvitationDialog } from '@/components/Dialogs/DeactivateInvitationDialog';
import { InviteUserDialog } from '@/components/Dialogs/InviteUserDialog';
import { PageHeader } from '@/components/PageHeader';
import ServerSideDataTable from '@/components/ServerSideDataTable';
import { useSnackbar } from '@/hooks/useSnackbar';
import { formatDate } from '@/utils/common';

const Invites = () => {
  const [data, setData] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [isInviteUserOpen, setIsInviteUserOpen] = useState(false);
  const [isDeactivateInviteOpen, setDeactivateInviteOpen] = useState(false);
  const [invitationId, setInvitationId] = useState(null);
  const [dataUpdatedAt, setDataUpdatedAt] = useState(new Date());

  const refreshInvites = useCallback(() => {
    setDataUpdatedAt(new Date());
  }, []);

  const pageHeaderActions = [
    {
      label: 'Invite User',
      icon: AddIcon,
      onClick: () => setIsInviteUserOpen(true),
      variant: 'contained',
    },
  ];

  const { showSuccess } = useSnackbar();

  const columns = useMemo(
    () => [
      {
        id: 'id',
        label: 'ID',
        sortable: true,
      },
      {
        id: 'type',
        label: 'Type',
        sortable: false,
        hidden: true,
        render: (row) =>
          row.type === 'email' ? (
            <Chip label='Email' variant='outlined' size='small' />
          ) : (
            <Chip label='Link' variant='outlined' size='small' />
          ),
      },
      {
        id: 'email',
        label: 'Email',
        sortable: true,
        render: (row) => (row.type === 'email' ? row.email : 'N/A'),
      },
      {
        id: 'token',
        label: 'Token',
        sortable: false,
        hidden: true,
      },
      {
        id: 'registered_user_email',
        label: 'Registered Users',
        sortable: true,
        width: 200,
        render: (row) => (
          <Stack direction='row' spacing={1} sx={{ flexWrap: 'wrap', gap: '8px' }}>
            {row.registered_users.map((user) => (
              <Chip key={user.id} label={user.email} clickable color='primary' size='small' />
            ))}
          </Stack>
        ),
      },
      {
        id: 'user_expiry_date',
        label: 'User Expiry Date',
        sortable: true,
        hidden: true,
        render: (row) => formatDate(row.user_expiry_date),
      },
      {
        id: 'created_at',
        label: 'Created At',
        sortable: true,
        render: (row) => formatDate(row.created_at),
      },
      {
        id: 'created_by_user_id',
        label: 'Created By',
        sortable: false,
        render: (row) => (
          <ListItemText
            primary={`${row.created_by_user.first_name} ${row.created_by_user.last_name}`}
            secondary={row.created_by_user.email}
          />
        ),
      },
      {
        id: 'expires_at',
        label: 'Expiry Date',
        sortable: true,
        hidden: true,
        render: (row) => formatDate(row.expires_at),
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
      filters
    ) => {
      try {
        setLoading(true);
        const requestBody = {
          order_by: orderBy,
          order: order.toLowerCase(),
          search: search,
          filters,
          limit: rowsPerPage,
          offset: page * rowsPerPage,
        };

        const response = await invitationsApi.getInvitationsDataTable(requestBody);

        setData(response.data.data || []);
        setTotalCount(response.data.count || 0);
      } catch (error) {
        console.error('Error fetching invitations:', error);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const copyLinkToClipboard = (token) => {
    navigator.clipboard.writeText(`${window.location.origin}/register?token=${token}`);
    showSuccess('Link copied to clipboard.');
  };

  const handleResendEmail = async (id) => {
    try {
      await invitationsApi.resendInvitation(id);
      showSuccess('Email resent successfully.');
    } catch (error) {
      console.error('Error resending invitation:', error);
    }
  };

  const rowActions = (row) => {
    if (!row.active) {
      return null;
    }

    return (
      <Stack direction='row' key={row.id} flexWrap='wrap' gap={1}>
        {row.type === 'email' && (
          <Button variant='outlined' size='small' onClick={() => handleResendEmail(row.id)}>
            Resend
          </Button>
        )}
        <Button variant='outlined' size='small' onClick={() => copyLinkToClipboard(row.token)}>
          Copy Link
        </Button>
        <Button
          variant='outlined'
          size='small'
          color='error'
          onClick={() => {
            setDeactivateInviteOpen(true);
            setInvitationId(row.id);
          }}
        >
          Deactivate
        </Button>
      </Stack>
    );
  };

  const types = [
    {
      label: 'Link',
      value: 'link',
    },
    {
      label: 'Email',
      value: 'email',
    },
  ];

  const statuses = [
    {
      label: 'Active',
      value: 'active',
    },
    {
      label: 'Registered',
      value: 'registered',
    },
    {
      label: 'Inactive',
      value: 'inactive',
    },
  ];

  // Define filter options for ServerSideDataTable
  const filters = [
    {
      id: 'status',
      label: 'Status',
      type: 'chips',
      options: statuses,
    },
    {
      id: 'type',
      label: 'Type',
      type: 'chips',
      options: types,
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

  return (
    <>
      <PageHeader
        title='Invitations'
        subtitle='Manage email invitations and registration links'
        actions={pageHeaderActions}
      />

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

      <InviteUserDialog
        open={isInviteUserOpen}
        handleClose={() => setIsInviteUserOpen(false)}
        onSuccess={refreshInvites}
      />
      <DeactivateInvitationDialog
        id={invitationId}
        open={isDeactivateInviteOpen}
        onClose={() => setDeactivateInviteOpen(false)}
        onSuccess={refreshInvites}
      />
    </>
  );
};

export default Invites;
