import { Box, CircularProgress } from '@mui/material';

export const Loader = ({ size = 40, color = 'primary', fullHeight = true, backdrop = false }) => {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: fullHeight ? '87vh' : '100%',
        width: '100%',
        ...(backdrop && {
          position: 'fixed',
          top: 0,
          left: 0,
          backgroundColor: 'rgba(255, 255, 255, 0.7)',
          zIndex: 9999,
        }),
      }}
    >
      <CircularProgress size={size} color={color} />
    </Box>
  );
};
