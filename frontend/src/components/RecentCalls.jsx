import React, { useEffect } from 'react';
import { Box, Typography, Card, CardContent, Divider, Chip, Alert } from '@mui/material';
import useConversationStore from '@/store/conversationStore';

const RecentCalls = () => {
  const sessions = useConversationStore((state) => state.sessions);
  const loading = useConversationStore((state) => state.loading);
  const fetchRecentSessions = useConversationStore((state) => state.fetchRecentSessions);

  // useEffect(() => {
  //   debugger
  //   fetchRecentSessions();
  // }, []);

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'in-progress': return 'warning';
      case 'queued': return 'info';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  // Helper to extract recording_sid from Twilio URL
  function recordingSidFromUrl(url) {
    if (!url) return '';
    const match = url.match(/Recordings\/([A-Za-z0-9]+)(\.mp3)?/);
    return match ? match[1] : '';
  }
  console.log('sessions', sessions)
  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>Recent Calls (Audio & Transcript)</Typography>
      
      {loading && <Typography>Loading recent calls...</Typography>}
      
      {!loading && sessions.length === 0 && (
        <Alert severity="info">
          No recent calls found. Make a call to see it appear here!
        </Alert>
      )}
      
      {sessions.map(session => (
        <Card key={session.id} sx={{ mb: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="subtitle1" fontWeight="bold">
                Call from: {session.from_number} to: {session.to_number}
              </Typography>
              <Chip 
                label={session.status} 
                color={getStatusColor(session.status)}
                size="small"
              />
            </Box>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {formatDate(session.created_at)}
            </Typography>
            
            {session.initial_message && (
              <Box sx={{ mb: 2, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="subtitle2" color="primary">
                  Initial Message:
                </Typography>
                <Typography variant="body2">
                  {session.initial_message}
                </Typography>
              </Box>
            )}
            
            <Divider sx={{ my: 1 }} />
            
            {session.interactions && session.interactions.length > 0 ? (
              session.interactions.map((interaction, idx) => (
                <Box key={interaction.id || idx} sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary">
                    Interaction {interaction.sequence} ({interaction.type})
                  </Typography>
                  
                  {interaction.transcript && (
                    <Box sx={{ mb: 1, p: 1, bgcolor: 'blue.50', borderRadius: 1 }}>
                      <Typography variant="body2">
                        <b>Transcript:</b> {interaction.transcript}
                      </Typography>
                      {interaction.confidence && (
                        <Typography variant="caption" color="text.secondary">
                          Confidence: {(interaction.confidence * 100).toFixed(1)}%
                        </Typography>
                      )}
                    </Box>
                  )}
                  
                  {interaction.audio_url && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" sx={{ mb: 0.5 }}>
                        <b>Audio Recording:</b>
                      </Typography>
                      <audio
                        controls
                        src={interaction.audio_url.startsWith('http')
                          ? `/api/calls/audio/${recordingSidFromUrl(interaction.audio_url)}`
                          : interaction.audio_url}
                        style={{ width: '100%' }}
                      >
                        Your browser does not support the audio element.
                      </audio>
                    </Box>
                  )}
                  
                  {interaction.recording_duration && (
                    <Typography variant="caption" color="text.secondary">
                      Duration: {interaction.recording_duration}s
                    </Typography>
                  )}
                  
                  <Divider sx={{ my: 1 }} />
                </Box>
              ))
            ) : (
              <Alert severity="info" sx={{ mt: 1 }}>
                No interactions recorded for this call. The call may have ended before any user response was captured.
              </Alert>
            )}
          </CardContent>
        </Card>
      ))}
    </Box>
  );
};

export default RecentCalls; 