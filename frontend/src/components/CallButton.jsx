import { useState, useEffect, useRef } from 'react';
import { Button, CircularProgress } from '@mui/material';
import { useSnackbar } from 'notistack';
import axios from 'axios';

const CallButton = () => {
  const [loading, setLoading] = useState(false);
  const [callStatus, setCallStatus] = useState('idle');
  const { enqueueSnackbar } = useSnackbar();
  const eventSourceRef = useRef(null);

  useEffect(() => {
    // Cleanup SSE connection on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const makeCall = async () => {
    setLoading(true);
    setCallStatus('initiating');
    try {
      const response = await axios.post(`/api/calls/make-call`, {
        to: '+14157981231',
        message: "Hello! How are you doing today?"
      });

      if (response.data.status === 'initiated') {
        const callSid = response.data.call_sid;
        enqueueSnackbar('Call initiated! You should receive it soon.', { variant: 'success' });

        // Connect to SSE stream
        const sseUrl = `/api/calls/stream/${callSid}`;
        console.log('Connecting to SSE:', sseUrl, 'CallSid:', callSid);
        const eventSource = new EventSource(sseUrl);
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
          console.log('SSE connection opened successfully');
        };

        eventSource.onmessage = (event) => {
          const data = JSON.parse(event.data);
          console.log('SSE message received:', data);
          setCallStatus(data.status);

          if (data.status === 'connected') {
            console.log('SSE connected, waiting for call updates...');
          } else if (data.status === 'in-progress') {
            console.log('In progress');
            enqueueSnackbar('Call in progress...', { variant: 'info' });
          } else if (data.status === 'completed') {
            console.log('Call completed with complete data:', {
              interactions: data.interactions,
              call_session: data.call_session,
              twilio_status: data.twilio_status
            });

            // Log each interaction
            if (data.interactions && data.interactions.length > 0) {
              console.log('Interactions:', data.interactions);
              data.interactions.forEach((interaction, index) => {
                console.log(`Interaction ${index + 1}:`, {
                  type: interaction.type,
                  sequence: interaction.sequence,
                  transcript: interaction.transcript,
                  audio_url: interaction.audio_url,  // USER's speech audio (transcript audio)
                  response: interaction.system_response,
                  system_audio_url: interaction.system_audio_url,  // AI's response audio
                  confidence: interaction.confidence
                });
              });
            }

            enqueueSnackbar(`Call ${data.twilio_status}!`, { variant: 'success' });
            setLoading(false);
            eventSource.close();
          }
        };

        eventSource.onerror = (error) => {
          console.log('SSE error occurred:', error);
          console.log('EventSource readyState:', eventSource.readyState);
          eventSource.close();
          setLoading(false);
        };
      } else {
        console.log('End Call')
        enqueueSnackbar('Failed to initiate call', { variant: 'error' });
        setLoading(false);
      }
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to make call', { variant: 'error' });
      setLoading(false);
      setCallStatus('idle');
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
      {loading ? (
        <span>
          <CircularProgress size={24} style={{ marginRight: 8 }} />
          {callStatus === 'initiating' && 'Initiating...'}
          {callStatus === 'in-progress' && 'In Progress...'}
          {callStatus === 'completed' && 'Completed!'}
        </span>
      ) : (
        'Call Now'
      )}
    </Button>
  );
};

export default CallButton; 