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
  const audioRefs = useRef({});
  const chatEndRef = useRef(null);
  const conversations = useConversationStore((state) => state.conversations);
  const setConversations = useConversationStore((state) => state.setConversations);

  // Get interactions from selectedUser[0] if available
  const sessionInteractions = selectedUser && selectedUser?.interactions?.length > 0 ?
   [{...selectedUser.interactions[0], transcript: selectedUser?.initial_message, sequence: 0 } , ...selectedUser.interactions] || [] : [];
  
  console.log('sessionInteractions', sessionInteractions)
  // Transform session interactions into conversation messages
  const messages = [];
  if (sessionInteractions.length > 0) {
    // Use session interactions
    sessionInteractions.forEach((interaction) => {
      // Determine sender based on sequence: even = sender, odd = receiver
      const isSender = interaction.sequence % 2 === 0;

      // Add user message if transcript exists
      if (interaction.transcript) {
        messages.push({
          sender: isSender ? 'sender' : 'receiver',
          text: interaction.transcript,
          audioUrl: interaction.audio_url,
          timestamp: new Date(interaction.created_at).getTime(),
          sequence: interaction.sequence,
        });
      }
      // Add AI response if system_response exists
      if (interaction.system_response) {
        messages.push({
          sender: isSender ? 'sender' : 'receiver',
          text: interaction.system_response,
          audioUrl: interaction.system_audio_url,
          timestamp: new Date(interaction.created_at).getTime() + 1,
          sequence: interaction.sequence,
        });
      }
    });
  } else {
    // Fallback to regular conversations
    messages.push(...(conversations[selectedUser] || []));
  }

  // useEffect(() => {
  //   if (chatEndRef.current) {
  //     chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
  //   }
  // }, [messages]);

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
    const audioElement = audioRefs.current[messageId];

    if (!audioElement) return;

    if (playingAudio === messageId) {
      // Pause the currently playing audio
      audioElement.pause();
      setPlayingAudio(null);
    } else {
      // Pause any other playing audio
      Object.keys(audioRefs.current).forEach((key) => {
        if (audioRefs.current[key] && key !== messageId.toString()) {
          audioRefs.current[key].pause();
        }
      });

      // Play the selected audio
      audioElement.play().catch((error) => {
        console.error('Error playing audio:', error);
      });
      setPlayingAudio(messageId);
    }
  };

  const renderAudioPlayer = (audioUrl, messageId) => {
    if (!audioUrl) return null;

    const isPlaying = playingAudio === messageId;

    return (
      <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
        <audio
          ref={(el) => {
            if (el) {
              audioRefs.current[messageId] = el;
            }
          }}
          src={audioUrl}
          onEnded={() => setPlayingAudio(null)}
          onPause={() => {
            if (playingAudio === messageId) {
              setPlayingAudio(null);
            }
          }}
          preload="metadata"
        />
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
  // console.log('messgaes', messages)
  return (
    <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box sx={{ flex: 1, p: 2, display: 'flex', flexDirection: 'column', gap: 2, overflowY: 'auto', minHeight: '300px' }}>
        {messages.map((msg, idx) => (
          <Box
            key={idx}
            sx={{
              alignSelf: msg.sender === 'sender' ? 'flex-end' : 'flex-start',
              bgcolor: msg.sender === 'sender' ? '#eee' : '#DCF8C6',
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
      {/* <Box sx={{ display: 'flex', p: 1, borderTop: '1px solid #ccc' }}>
        <TextField
          fullWidth
          placeholder="Enter message"
          size="small"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleInputKeyDown}
        />
        <Button variant="contained" sx={{ ml: 1 }} onClick={handleSend}>Send</Button>
      </Box> */}
    </Box>
  );
} 