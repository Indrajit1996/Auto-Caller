import { Box, Button, Container, Typography } from '@mui/material';
import { useNavigate } from 'react-router';

import { ROUTES } from '@/constants/routeConstants';

const ErrorPage = ({
  code = '404',
  title = 'Page Not Found',
  description = 'The page you are looking for does not exist.',
  actionText = 'Go to Home',
  actionPath = ROUTES.LOGGED_IN_HOME,
  showAction = true,
}) => {
  const navigate = useNavigate();

  const handleAction = () => {
    navigate(actionPath);
  };

  return (
    <Container>
      <Box
        sx={{
          minHeight: '87vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          textAlign: 'center',
          py: 4,
        }}
      >
        <Typography
          variant='h1'
          component='h1'
          gutterBottom
          sx={{
            fontSize: { xs: '4rem', sm: '6rem' },
            fontWeight: 'bold',
          }}
        >
          {code}
        </Typography>

        <Typography variant='h5' component='h2' gutterBottom sx={{ mb: 2 }}>
          {title}
        </Typography>

        <Typography variant='body1' color='text.secondary' gutterBottom sx={{ mb: 4 }}>
          {description}
        </Typography>

        {showAction && (
          <Button variant='contained' color='primary' onClick={handleAction} size='large'>
            {actionText}
          </Button>
        )}
      </Box>
    </Container>
  );
};

export default ErrorPage;
