import { Dialog, DialogTitle } from '@mui/material';

/**
 * A dialog component that persists until explicitly closed
 * Prevents accidental dismissal by disabling backdrop click
 * Ideal for forms and important confirmations
 *
 * @param {Object} props
 * @param {boolean} props.open - Controls dialog visibility
 * @param {Function} props.onClose - Handler called when dialog should close
 * @param {string} props.title - Dialog title text
 * @param {boolean} [props.isForm=false] - If true, wraps content in a form element
 * @param {Function} [props.onSubmit] - Form submit handler, required if isForm is true
 * @param {React.ReactNode} props.children - Dialog content
 * @returns {React.ReactElement} Dialog component
 */

export const PersistentDialog = ({
  open,
  onClose,
  title,
  isForm = false,
  onSubmit,
  children,
  ...props
}) => {
  const paperProps = isForm
    ? {
        component: 'form',
        onSubmit,
      }
    : {};

  return (
    <Dialog
      open={open}
      onClose={(event, reason) => {
        if (reason === 'backdropClick') return;
        onClose?.(event, reason);
      }}
      disableEscapeKeyDown
      fullWidth
      PaperProps={paperProps}
      {...props}
    >
      {title && <DialogTitle>{title}</DialogTitle>}
      <>{children}</>
    </Dialog>
  );
};
