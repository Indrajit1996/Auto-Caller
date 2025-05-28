import { useCallback, useEffect, useState } from 'react';

import notificationsApi from '@/api/notifications';

export const useNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const response = await notificationsApi.getNotifications();
      setNotifications(response.data);
      setUnreadCount(response.data.filter((notification) => !notification.is_read).length);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to fetch notifications');
    } finally {
      setLoading(false);
    }
  }, []);

  const markAsRead = useCallback(async (notificationId) => {
    try {
      const updatedNotification = await notificationsApi.markAsRead(notificationId);
      // Remove the notification from the list once marked as read
      setNotifications((prevNotifications) =>
        prevNotifications.filter((notification) => notification.id !== notificationId)
      );
      setUnreadCount((prevCount) => Math.max(0, prevCount - 1));
      return updatedNotification;
    } catch (err) {
      setError(err.message || 'Failed to mark notification as read');
      throw err;
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      await notificationsApi.markAllAsRead();
      setNotifications([]);
      setUnreadCount(0);
      return true;
    } catch (err) {
      setError(err.message || 'Failed to mark all notifications as read');
      throw err;
    }
  }, []);

  // Fetch notifications initially and set up auto-refresh
  useEffect(() => {
    fetchNotifications();
    const intervalId = setInterval(fetchNotifications, 600000); // Refresh every 10 minutes

    return () => clearInterval(intervalId);
  }, [fetchNotifications]);

  return {
    notifications,
    loading,
    error,
    unreadCount,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
  };
};
