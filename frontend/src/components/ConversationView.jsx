import React, { useRef, useEffect, useState } from 'react';
import { Box, TextField, Button } from '@mui/material';
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