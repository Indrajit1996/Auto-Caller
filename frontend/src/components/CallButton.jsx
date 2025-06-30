import { useState } from 'react';
import { Button, CircularProgress } from '@mui/material';
import { useSnackbar } from 'notistack';
import axios from 'axios';

const randomMessages = [
  'This is a random test call from Auto-Caller!',
  'Hello! This is your friendly automated call.',
  'Testing, testing, 1-2-3!',
  'Have a great day from Auto-Caller!',
  'This is an immediate call demo.'
];

function getRandomMessage() {
  return randomMessages[Math.floor(Math.random() * randomMessages.length)];
}

const CallButton = () => {
  const [loading, setLoading] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  const makeCall = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`/api/calls/make-call`, {
        to: '+16023860501',
        message: getRandomMessage()
      });
      if (response.data.status === 'initiated') {
        enqueueSnackbar('Call initiated! You should receive it soon.', { variant: 'success' });
      } else {
        enqueueSnackbar('Failed to initiate call', { variant: 'error' });
      }
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to make call', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      variant="contained"
      color="primary"
      onClick={makeCall}
      disabled={loading}
      sx={{ mt: 2 }}
    >
      {loading ? <CircularProgress size={24} /> : 'Call Now'}
    </Button>
  );
};

export default CallButton; 