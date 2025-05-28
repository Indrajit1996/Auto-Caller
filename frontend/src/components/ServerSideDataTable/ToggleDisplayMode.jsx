import ViewCompactIcon from '@mui/icons-material/ViewCompact';
import ViewStreamIcon from '@mui/icons-material/ViewStream';
import { Button } from '@mui/material';

/**
 * Toggle between compact and normal table display modes
 * Using a button with both text and icon for clarity
 */
const ToggleDisplayMode = ({ isCompact, onToggle }) => {
  // Toggle the current state
  const handleToggle = () => {
    onToggle(!isCompact);
  };

  return (
    <Button
      variant='outlined'
      color={isCompact ? 'primary' : 'neutral'}
      onClick={handleToggle}
      startIcon={isCompact ? <ViewCompactIcon /> : <ViewStreamIcon />}
    >
      {isCompact ? 'Compact' : 'Normal'}
    </Button>
  );
};

export default ToggleDisplayMode;
