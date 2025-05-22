import { useCallback, useEffect, useMemo, useState } from 'react';

import { Box, Button, Checkbox, DialogActions, DialogContent } from '@mui/material';

import groupsApi from '@/api/groups';
import { PersistentDialog } from '@/components/PersistentDialog';
import ServerSideDataTable from '@/components/ServerSideDataTable';
import { useSnackbar } from '@/hooks/useSnackbar';

export const AddUsersToGroupDialog = ({ open, onClose, groupId, onUsersAdded }) => {
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState({ data: [], total: 0 });
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [existingUsers, setExistingUsers] = useState([]);
  const { showSuccess, showError } = useSnackbar();

  const handleSelectAll = useCallback(
    (checked) => {
      if (checked) {
        const allUserIds = users.data.map((user) => user.id);
        setSelectedUsers(allUserIds);
      } else {
        setSelectedUsers([]);
      }
    },
    [users.data]
  );

  const columns = useMemo(
    () => [
      {
        id: 'checkbox',
        label: (
          <Checkbox
            checked={users.data.length > 0 && selectedUsers.length === users.data.length}
            indeterminate={selectedUsers.length > 0 && selectedUsers.length < users.data.length}
            onChange={(e) => handleSelectAll(e.target.checked)}
          />
        ),
        sortable: false,
        width: '50px',
      },
      { id: 'first_name', label: 'First Name', sortable: true },
      { id: 'last_name', label: 'Last Name', sortable: true },
      { id: 'email', label: 'Email', sortable: true },
    ],
    [users.data.length, selectedUsers.length, handleSelectAll]
  );

  const fetchUsers = useCallback(
    async (page = 0, rowsPerPage = 10, orderBy = 'created_at', order = 'desc', search = '') => {
      if (!open || !groupId) return;

      setLoading(true);
      try {
        const response = await groupsApi.getAvailableUsers({
          offset: page * rowsPerPage,
          limit: rowsPerPage,
          search: search,
          filters: {
            status: 'active',
            role: 'all',
            group: 'all',
            exclude_group: groupId,
          },
          order_by: orderBy,
          order: order.toLowerCase(),
        });

        setUsers({
          data: response.data.data || [],
          total: response.data.count || 0,
        });
      } catch (error) {
        showError(error.response?.data?.message || 'Failed to fetch users');
      } finally {
        setLoading(false);
      }
    },
    [open, groupId, showError]
  );

  const fetchExistingUsers = useCallback(async () => {
    if (!open || !groupId) return;

    try {
      const response = await groupsApi.getGroupUsers({
        offset: 0,
        limit: 100,
        search: '',
        filters: {
          status: 'all',
          role: 'all',
          group: groupId,
        },
        order_by: 'created_at',
        order: 'desc',
      });
      setExistingUsers(response.data.data.map((user) => user.id));
    } catch (error) {
      showError(error.response?.data?.message || 'Failed to fetch existing users');
    }
  }, [open, groupId, showError]);

  const handleAddUsers = useCallback(async () => {
    try {
      const allUserIds = [...new Set([...existingUsers, ...selectedUsers])];
      await groupsApi.addUsersToGroup(groupId, allUserIds);
      showSuccess('Users successfully added to group');
      onUsersAdded();
      onClose();
    } catch (error) {
      showError(error.response?.data?.message || 'Failed to add users');
    }
  }, [groupId, existingUsers, selectedUsers, showSuccess, showError, onUsersAdded, onClose]);

  useEffect(() => {
    if (open) {
      setSelectedUsers([]);
      setUsers({ data: [], total: 0 }); // Reset users data
      fetchExistingUsers();
    }
  }, [open, fetchExistingUsers]);

  return (
    <PersistentDialog
      open={open}
      onClose={onClose}
      onSubmit={handleAddUsers}
      isForm
      title={
        selectedUsers.length === 0
          ? 'Add Users to Group'
          : `Add ${selectedUsers.length} ${selectedUsers.length === 1 ? 'User' : 'Users'} to Group`
      }
    >
      <DialogContent dividers>
        <Box sx={{ mt: 2 }}>
          <ServerSideDataTable
            data={users.data.map((user) => ({
              ...user,
              checkbox: (
                <Checkbox
                  checked={selectedUsers.includes(user.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedUsers((prev) => [...prev, user.id]);
                    } else {
                      setSelectedUsers((prev) => prev.filter((id) => id !== user.id));
                    }
                  }}
                />
              ),
            }))}
            columns={columns}
            totalCount={users.total}
            defaultSort={{ order: 'desc', orderBy: 'created_at' }}
            defaultRowsPerPage={10}
            loading={loading}
            persistState={false}
            fetchData={fetchUsers}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} variant='outlined' color='neutral'>
          Cancel
        </Button>
        <Button variant='contained' onClick={handleAddUsers} disabled={selectedUsers.length === 0}>
          Add Selected Users
        </Button>
      </DialogActions>
    </PersistentDialog>
  );
};
