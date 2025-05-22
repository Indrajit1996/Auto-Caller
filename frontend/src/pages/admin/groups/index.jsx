import { useCallback, useMemo, useState } from 'react';

import { Add as AddIcon } from '@mui/icons-material';
import { Button, ListItemText, Stack } from '@mui/material';
import { useNavigate } from 'react-router';
import { Link as RouterLink } from 'react-router';

import groupsApi from '@/api/groups';
import { CreateGroupDialog } from '@/components/Dialogs/CreateGroupDialog';
import { DeleteGroupDialog } from '@/components/Dialogs/DeleteGroupDialog';
import { EditGroupDialog } from '@/components/Dialogs/EditGroupDialog';
import { PageHeader } from '@/components/PageHeader';
import ServerSideDataTable from '@/components/ServerSideDataTable';
import { ROUTES } from '@/constants/routeConstants';
import { useSnackbar } from '@/hooks/useSnackbar';
import { formatDate } from '@/utils/common';

const Groups = () => {
  const [groups, setGroups] = useState({});
  const [loading, setLoading] = useState(true);
  const { showError } = useSnackbar();
  const [isAddGroupModalOpen, setIsAddGroupModalOpen] = useState(false);
  const [isDeleteGroupDialogOpen, setIsDeleteGroupDialogOpen] = useState(false);
  const [isEditGroupDialogOpen, setIsEditGroupDialogOpen] = useState(false);
  const [groupToDelete, setGroupToDelete] = useState(null);
  const [groupToEdit, setGroupToEdit] = useState(null);
  const [dataUpdatedAt, setDataUpdatedAt] = useState(new Date());

  const navigate = useNavigate();

  const refreshGroups = useCallback(() => {
    setDataUpdatedAt(new Date());
  }, []);

  const pageHeaderActions = [
    {
      label: 'Add Group',
      icon: AddIcon,
      onClick: () => setIsAddGroupModalOpen(true),
      variant: 'contained',
    },
  ];

  const handleEditGroup = (groupId) => {
    setGroupToEdit(groupId);
    setIsEditGroupDialogOpen(true);
  };

  const columns = useMemo(
    () => [
      {
        id: 'name',
        label: 'Name',
        sortable: true,
        render: (row) => (
          <Button
            variant='text'
            component={RouterLink}
            to={ROUTES.ADMIN.GROUP_DETAIL.replace(':groupId', row.id)}
            sx={{ textTransform: 'none' }}
          >
            {row.name}
          </Button>
        ),
      },
      { id: 'description', label: 'Description', hidden: true },
      { id: 'user_count', label: 'Total Users', sortable: false, render: (row) => row.user_count },
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
        id: 'created_at',
        label: 'Created At',
        sortable: true,
        render: (row) => formatDate(row.created_at),
      },
      {
        id: 'actions',
        label: 'Actions',
        sortable: false,
        render: (row) => (
          <Stack direction='row' spacing={1} key={row.id}>
            <Button
              size='small'
              variant='outlined'
              color='neutral'
              onClick={() => handleEditGroup(row.id)}
            >
              Edit
            </Button>
            <Button
              size='small'
              variant='outlined'
              color='error'
              onClick={() => handleDeleteGroup(row.id)}
            >
              Delete
            </Button>
          </Stack>
        ),
      },
    ],
    []
  );

  const fetchGroups = useCallback(
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
          order_by: orderBy,
          order,
          page,
          rows_per_page: rowsPerPage,
          search,
          filters,
        };
        const response = await groupsApi.getGroupsDataTable(requestBody);

        setGroups({
          data: response.data.data || [],
          total: response.data.count || 0,
        });
      } catch (error) {
        showError(error.response?.data?.message || 'Failed to fetch groups');
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const handleDeleteGroup = (groupId) => {
    setGroupToDelete(groupId);
    setIsDeleteGroupDialogOpen(true);
  };

  return (
    <>
      <PageHeader
        title='Groups'
        subtitle='Manage groups in the system'
        actions={pageHeaderActions}
      />

      <ServerSideDataTable
        data={groups?.data || []}
        columns={columns}
        totalCount={groups?.total || 0}
        defaultSort={{ order: 'desc', orderBy: 'created_at' }}
        defaultRowsPerPage={10}
        loading={loading}
        filters={[]}
        defaultFilters={{}}
        fetchData={fetchGroups}
        refreshDataTrigger={dataUpdatedAt}
      />

      <CreateGroupDialog
        open={isAddGroupModalOpen}
        onClose={() => setIsAddGroupModalOpen(false)}
        onGroupAdded={() => {
          setIsAddGroupModalOpen(false);
          refreshGroups();
        }}
      />
      <DeleteGroupDialog
        open={isDeleteGroupDialogOpen}
        onClose={() => {
          setIsDeleteGroupDialogOpen(false);
          setGroupToDelete(null);
        }}
        groupId={groupToDelete}
        onSuccess={refreshGroups}
      />
      <EditGroupDialog
        open={isEditGroupDialogOpen}
        onClose={() => {
          setIsEditGroupDialogOpen(false);
          setGroupToEdit(null);
        }}
        id={groupToEdit}
        onSuccess={refreshGroups}
      />
    </>
  );
};

export default Groups;
