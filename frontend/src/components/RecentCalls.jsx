import React, { useEffect, useState } from 'react';
import { Box, Typography, Card, CardContent, Divider } from '@mui/material';
import api from '@/api';

const RecentCalls = () => {
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    api.getRecentCallInteractions().then(res => {
      if (res.data && res.data.sessions) setSessions(res.data.sessions);
    });
  }, []);

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>Recent Calls (Audio & Transcript)</Typography>
      {sessions.length === 0 && <Typography>No recent calls found.</Typography>}
      {sessions.map(session => (
        <Card key={session.id} sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle1">
              Call from: {session.from_number} to: {session.to_number}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {session.created_at}
            </Typography>
            <Divider sx={{ my: 1 }} />
            {session.interactions.map((interaction, idx) => (
              <Box key={interaction.id || idx} sx={{ mb: 2 }}>
                <Typography variant="subtitle2">
                  Interaction {interaction.sequence} ({interaction.type})
                </Typography>
                {interaction.transcript && (
                  <Typography sx={{ mb: 1 }}>
                    <b>Transcript:</b> {interaction.transcript}
                  </Typography>
                )}
                {interaction.audio_url && (
                  <audio controls src={interaction.audio_url} style={{ width: '100%' }}>
                    Your browser does not support the audio element.
                  </audio>
                )}
                <Divider sx={{ my: 1 }} />
              </Box>
            ))}
          </CardContent>
        </Card>
      ))}
    </Box>
  );
};

export default RecentCalls; 