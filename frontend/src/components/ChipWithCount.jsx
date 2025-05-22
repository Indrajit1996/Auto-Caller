import { Chip } from '@mui/material';
import { styled } from '@mui/material';

const CountBadge = styled(Chip)(({ theme }) => ({
  height: '20px',
  marginLeft: theme.spacing(1),
  '& .MuiChip-label': {
    padding: '0 6px',
    fontSize: '0.75rem',
  },
  color: theme.palette.common.white,
}));

const StatusChip = styled(Chip, {
  shouldForwardProp: (prop) => prop !== 'isActive',
})(({ theme, isActive }) => ({
  padding: theme.spacing(0.5),
  '&:hover': {
    backgroundColor: isActive ? theme.palette.primary.dark : theme.palette.grey[300],
  },
  transition: 'all 0.2s ease-in-out',
}));

export const ChipWithCount = ({ count, label, value, handleOnClick, isActive }) => {
  return (
    <StatusChip
      clickable
      isActive={isActive}
      color={isActive ? 'primary' : 'default'}
      onClick={() => handleOnClick(value)}
      label={
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {label}
          {count > 0 && (
            <CountBadge label={count} color={isActive ? 'default' : 'primary'} size='small' />
          )}
        </div>
      }
    />
  );
};
