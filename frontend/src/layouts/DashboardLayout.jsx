import { Outlet } from 'react-router';
import { useEffect, useState } from 'react';

import { AppLayout } from '@/layouts/base/AppLayout';
import { ProtectedLayout } from '@/layouts/base/ProtectedLayout';
import api from '@/api';

export const DashboardLayout = () => {
  const isSevenScreen = import.meta.env.VITE_SEVEN_SCREEN_DASHBOARD_LAYOUT_ENABLED === 'true';
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchConversations = async () => {
      debugger
      try {
        const response = await api.get('/conversations');
        setConversations(response.data);
      } catch (error) {
        console.error('Failed to fetch conversations:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchConversations();
  }, []);

  return (
    <ProtectedLayout>
      {isSevenScreen ? (
        <Outlet />
      ) : (
        <AppLayout>
          <Outlet />
        </AppLayout>
      )}
    </ProtectedLayout>
  );
};
