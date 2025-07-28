import React, { useRef, useEffect, useState } from 'react';
import { Box, TextField, Button, IconButton, Typography } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import useConversationStore from '@/store/conversationStore';

function getSimulatedElapsedForText(text) {
  // Use WPM = 140
  const WPM = 140;
  const words = text.trim().split(/\s+/).length;
  const elapsed = (60 / WPM) * words;
  return Math.max(1, Math.round(elapsed));
}

export default function ConversationView({
  selectedUser,
  sidebarUsers,
  onSummaryUpdate,
}) {
  const [input, setInput] = useState('');
  const [playingAudio, setPlayingAudio] = useState(null);
  const chatEndRef = useRef(null);
  const conversations = useConversationStore((state) => state.conversations);
  const setConversations = useConversationStore((state) => state.setConversations);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversations, selectedUser]);

  const handleSend = () => {
    if (!input.trim()) return;
    const now = Date.now();
    const simulatedElapsed = getSimulatedElapsedForText(input);
    setConversations((prev) => ({
      ...prev,
      [selectedUser]: [
        ...(prev[selectedUser] || []),
        { sender: 'user', text: input, timestamp: now, simulatedElapsed },
      ],
    }));
    setInput('');
    // Simulate bot reply after the same elapsed time
    const botText = 'Bot: Got it!';
    setTimeout(() => {
      setConversations((prev) => ({
        ...prev,
        [selectedUser]: [
          ...(prev[selectedUser] || []),
          {
            sender: 'bot',
            text: botText,
            timestamp: Date.now(),
          },
        ],
      }));
    }, simulatedElapsed * 1000);
  };

  const handleInputKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault(); // prevent form submission or new line
      handleSend();
    }
  };

  const handleAudioPlay = (audioUrl, messageId) => {
    if (playingAudio === messageId) {
      // Stop playing
      setPlayingAudio(null);
      // You could add logic to stop the audio here
    } else {
      // Start playing new audio
      setPlayingAudio(messageId);
      // You could add logic to play the audio here
      console.log('Playing audio:', audioUrl);
    }
  };

  const renderAudioPlayer = (audioUrl, messageId) => {
    if (!audioUrl) return null;
    
    const isPlaying = playingAudio === messageId;
    
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
        <IconButton
          size="small"
          onClick={() => handleAudioPlay(audioUrl, messageId)}
          sx={{ mr: 1 }}
        >
          {isPlaying ? <PauseIcon /> : <PlayArrowIcon />}
        </IconButton>
        <VolumeUpIcon sx={{ fontSize: 16, mr: 1 }} />
        <Typography variant="caption" color="text.secondary">
          Audio Message
        </Typography>
      </Box>
    );
  };

  return (
    <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box sx={{ flex: 1, p: 2, display: 'flex', flexDirection: 'column', gap: 2, overflowY: 'auto', minHeight: '300px' }}>
        {(conversations[selectedUser] || []).map((msg, idx) => (
          <Box
            key={idx}
            sx={{
              alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              bgcolor: msg.sender === 'user' ? '#eee' : '#e3f2fd',
              p: 1,
              borderRadius: 2,
              maxWidth: '60%',
              wordBreak: 'break-word',
            }}
          >
            {msg.text}
            {renderAudioPlayer(msg.audioUrl, idx)}
          </Box>
        ))}
        <div ref={chatEndRef} />
      </Box>
      <Box sx={{ display: 'flex', p: 1, borderTop: '1px solid #ccc' }}>
        <TextField
          fullWidth
          placeholder="Enter message"
          size="small"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleInputKeyDown}
        />
        <Button variant="contained" sx={{ ml: 1 }} onClick={handleSend}>Send</Button>
      </Box>
    </Box>
  );
} 