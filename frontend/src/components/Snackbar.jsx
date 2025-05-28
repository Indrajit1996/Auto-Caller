import { createContext } from 'react';

import CloseIcon from '@mui/icons-material/Close';
import IconButton from '@mui/material/IconButton';
import {
  SnackbarProvider as NotistackProvider,
  useSnackbar as useNotistackSnackbar,
} from 'notistack';

const AUTO_HIDE_DURATION = 7000;

export const SnackbarContext = createContext();

const NotistackWrapper = ({ children }) => {
  const { enqueueSnackbar, closeSnackbar } = useNotistackSnackbar();

  const showSuccess = (message) => {
    enqueueSnackbar(message, {
      variant: 'success',
      anchorOrigin: { vertical: 'top', horizontal: 'right' },
      autoHideDuration: AUTO_HIDE_DURATION,
      action: (key) => (
        <IconButton onClick={() => closeSnackbar(key)} color='inherit'>
          <CloseIcon />
        </IconButton>
      ),
    });
  };

  const showError = (message) => {
    enqueueSnackbar(message, {
      variant: 'error',
      anchorOrigin: { vertical: 'top', horizontal: 'right' },
      autoHideDuration: AUTO_HIDE_DURATION,
      action: (key) => (
        <IconButton onClick={() => closeSnackbar(key)} color='inherit'>
          <CloseIcon />
        </IconButton>
      ),
    });
  };

  const showInfo = (message) => {
    enqueueSnackbar(message, {
      variant: 'info',
      anchorOrigin: { vertical: 'top', horizontal: 'right' },
      autoHideDuration: AUTO_HIDE_DURATION,
      action: (key) => (
        <IconButton onClick={() => closeSnackbar(key)} color='inherit'>
          <CloseIcon />
        </IconButton>
      ),
    });
  };

  const showWarning = (message) => {
    enqueueSnackbar(message, {
      variant: 'warning',
      anchorOrigin: { vertical: 'top', horizontal: 'right' },
      autoHideDuration: AUTO_HIDE_DURATION,
      action: (key) => (
        <IconButton onClick={() => closeSnackbar(key)} color='inherit'>
          <CloseIcon />
        </IconButton>
      ),
    });
  };

  return (
    <SnackbarContext.Provider value={{ showSuccess, showError, showInfo, showWarning }}>
      {children}
    </SnackbarContext.Provider>
  );
};

export const SnackbarProvider = ({ children }) => {
  return (
    <NotistackProvider maxSnack={5}>
      <NotistackWrapper>{children}</NotistackWrapper>
    </NotistackProvider>
  );
};
