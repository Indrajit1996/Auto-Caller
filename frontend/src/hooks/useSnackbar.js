import { useContext } from 'react';

import { SnackbarContext } from '@/components/Snackbar';

/**
 * A hook that provides snackbar functionality
 * @typedef {Object} SnackbarHook
 * @property {Function} showSuccess Shows a success message snackbar
 * @property {Function} showError Shows an error message snackbar
 * @property {Function} showInfo Shows an info message snackbar
 * @property {Function} showWarning Shows a warning message snackbar
 */

/**
 * Custom hook for accessing the global snackbar functionality
 * @returns {SnackbarHook} An object containing showSuccess and showError functions
 * @example
 * const { showSuccess, showError, showInfo, showWarning } = useSnackbar();
 * showSuccess('Operation successful!');
 * showError('Something went wrong!');
 */

export const useSnackbar = () => {
  const context = useContext(SnackbarContext);
  if (!context) {
    throw new Error('useSnackbar must be used within a SnackbarProvider');
  }
  return context;
};
