import { useState } from 'react';
import { Button, CircularProgress } from '@mui/material';
import { useSnackbar } from 'notistack';
import axios from 'axios';

const CallButton = () => {
  const [loading, setLoading] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  const makeCall = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`/api/calls/make-call`, {
        to: '+16023860501',
        message: "Hello! This is your friendly automated call! I am here to check in on you and see how you are doing today."
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