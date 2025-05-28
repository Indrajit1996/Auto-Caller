import ErrorIcon from '@mui/icons-material/Error';
import { Box, Button, Container, Stack, Typography } from '@mui/material';
import { ErrorBoundary as ReactErrorBoundary } from 'react-error-boundary';

const ErrorFallback = ({ error, resetErrorBoundary }) => (
  <Container maxWidth='lg'>
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '80vh',
        textAlign: 'center',
        gap: 2,
        py: 8,
      }}
    >
      <ErrorIcon color='error' sx={{ fontSize: 64 }} />
      <Typography variant='h4' gutterBottom>
        Oops! Something went wrong
      </Typography>
      <Typography variant='body1' color='text.secondary'>
        {error?.message || 'An unexpected error occurred'}
      </Typography>
      <Stack direction='row' spacing={2}>
        <Button variant='contained' onClick={resetErrorBoundary}>
          Try Again
        </Button>
        <Button
          variant='outlined'
          onClick={() => {
            localStorage.clear();
            window.location.reload();
          }}
        >
          Clear Cache
        </Button>
      </Stack>
      {import.meta.env.MODE === 'development' && (
        <Box sx={{ mt: 4, textAlign: 'left' }}>
          <Typography variant='overline' display='block' gutterBottom>
            Error Details:
          </Typography>
          <pre
            style={{
              whiteSpace: 'pre-wrap',
              backgroundColor: '#f5f5f5',
              padding: '1rem',
              borderRadius: '4px',
            }}
          >
            {error?.stack}
          </pre>
        </Box>
      )}
    </Box>
  </Container>
);

export const ErrorBoundary = ({ children }) => {
  const handleError = (error, info) => {
    // Log to error reporting service
    console.error('Error:', error);
    console.error('Error Info:', info);
  };

  const handleReset = () => {
    // Reset any state if needed
    window.location.reload();
  };

  return (
    <ReactErrorBoundary
      FallbackComponent={ErrorFallback}
      onReset={handleReset}
      onError={handleError}
    >
      {children}
    </ReactErrorBoundary>
  );
};
