import { StrictMode, Suspense, useEffect } from 'react';

import { ThemeProvider } from '@emotion/react';
import CssBaseline from '@mui/material/CssBaseline';

import { ErrorBoundary } from '@/components/ErrorBoundary';
import { Loader } from '@/components/Loader';
import { SnackbarProvider } from '@/components/Snackbar';
import { useAuth } from '@/hooks';
import { Router } from '@/routes';
import theme from '@/theme';
import ScheduleCallForm from './components/ScheduleCallForm';

export const App = () => {
  const { initializeAuth } = useAuth();

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  return (
    <StrictMode>
      <ErrorBoundary>
        <ThemeProvider theme={theme} defaultMode='light'>
          <SnackbarProvider>
            <CssBaseline />
            <Suspense fallback={<Loader />}>
              <Router />
              <ScheduleCallForm />
            </Suspense>
          </SnackbarProvider>
        </ThemeProvider>
      </ErrorBoundary>
    </StrictMode>
  );
};
