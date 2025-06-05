import { useEffect, useState } from 'react';

import styled from '@emotion/styled';
import { WarningAmberOutlined } from '@mui/icons-material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import DoneIcon from '@mui/icons-material/Done';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import InfoIcon from '@mui/icons-material/Info';
import NotificationsIcon from '@mui/icons-material/Notifications';
import {
  Badge,
  Box,
  Button,
  CircularProgress,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Popover,
  Typography,
} from '@mui/material';

import { useNotifications } from '@/hooks/useNotifications';
import { formatDate } from '@/utils/common';

const StyledListItem = styled(ListItem)(({ theme }) => ({
  padding: theme.spacing(1.5, 1),
  cursor: 'pointer',
  marginBottom: theme.spacing(0.5),
  transition: 'transform 0.2s ease',
  '&:hover': {
    backgroundColor: theme.palette.action.hover,
    transform: 'scale(1.02)',
  },
  position: 'relative',
  '&:not(:last-child)::after': {
    content: '""',
    position: 'absolute',
    bottom: -4,
    left: 2,
    right: 2,
    height: 1,
    backgroundColor: theme.palette.divider,
  },
}));

const NotificationIcon = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  marginRight: theme.spacing(1.5),
}));

const NotificationContent = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isread',
})(({ isread }) => ({
  opacity: isread ? 0.7 : 1,
  width: '100%',
  overflow: 'hidden',
}));

const NotificationPanel = () => {
  const [anchorEl, setAnchorEl] = useState(null);
  const { notifications, loading, unreadCount, markAsRead, fetchNotifications, markAllAsRead } =
    useNotifications();

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleMarkAsRead = async (notificationId) => {
    await markAsRead(notificationId);
  };

  const handleMarkAllAsRead = async () => {
    await markAllAsRead();
  };

  const open = Boolean(anchorEl);
  const id = open ? 'notification-popover' : undefined;

  const renderNotificationIcon = (type) => {
    switch (type) {
      case 'error':
        return <ErrorOutlineIcon color='error' />;
      case 'warning':
        return <WarningAmberOutlined color='warning' />;
      case 'success':
        return <CheckCircleOutlineIcon color='success' />;
      case 'info':
        return <InfoIcon color='info' />;
      default:
        return <NotificationsIcon color='action' />;
    }
  };

  return (
    <>
      <IconButton color='inherit' aria-label='notifications' onClick={handleOpen}>
        <Badge badgeContent={unreadCount} color='error'>
          <NotificationsIcon />
        </Badge>
      </IconButton>
      <Popover
        id={id}
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <Box sx={{ width: 350, maxHeight: 500 }}>
          <Box
            sx={{
              p: 2,
              borderBottom: '1px solid',
              borderColor: 'divider',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Typography variant='subtitle1' fontWeight='bold'>
              Notifications
            </Typography>
            {notifications.length > 0 && (
              <Button size='small' onClick={handleMarkAllAsRead} color='primary'>
                Mark all as read
              </Button>
            )}
          </Box>
          {loading ? (
            <Box display='flex' justifyContent='center' p={3}>
              <CircularProgress size={30} />
            </Box>
          ) : notifications.length === 0 ? (
            <Box p={3} textAlign='center'>
              <Typography variant='body2' color='text.secondary'>
                No new notifications
              </Typography>
            </Box>
          ) : (
            <List sx={{ p: 1, maxHeight: 400, overflow: 'auto' }}>
              {notifications.map((notification) => (
                <StyledListItem
                  key={notification.id}
                  disableGutters
                  secondaryAction={
                    !notification.is_read && (
                      <IconButton
                        edge='end'
                        aria-label='mark as read'
                        onClick={(e) => {
                          e.stopPropagation();
                          handleMarkAsRead(notification.id);
                        }}
                        sx={{ mr: 1 }}
                      >
                        <DoneIcon fontSize='small' />
                      </IconButton>
                    )
                  }
                >
                  <NotificationIcon>{renderNotificationIcon(notification.type)}</NotificationIcon>
                  <NotificationContent isread={notification.is_read}>
                    <ListItemText
                      primary={
                        <Typography variant='body2' maxWidth='87%'>
                          {notification.message}
                        </Typography>
                      }
                      secondary={
                        <Typography variant='caption' color='text.secondary'>
                          {formatDate(notification.created_at)}
                        </Typography>
                      }
                    />
                  </NotificationContent>
                </StyledListItem>
              ))}
            </List>
          )}
        </Box>
      </Popover>
    </>
  );
};

export default NotificationPanel;
