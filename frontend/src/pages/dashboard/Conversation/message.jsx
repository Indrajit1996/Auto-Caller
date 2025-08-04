import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Button, Divider, Grid2 as Grid, TextField, Typography, Box } from '@mui/material';

import { useAuth } from '@/hooks';
import { ROUTES } from '@/constants/routeConstants'

const Message = (props) => {
  const messages = props?.messages || [];

  const containerStyle = {
    height: '100vh',
    backgroundColor: '#0f1419',
    position: 'relative',
    overflow: 'hidden',
    backgroundImage: `
      radial-gradient(circle at 25px 25px, rgba(255,255,255,0.05) 1px, transparent 1px),
      radial-gradient(circle at 75px 75px, rgba(255,255,255,0.03) 1px, transparent 1px)
    `,
    backgroundSize: '50px 50px, 100px 100px',
  };

  const chatContainerStyle = {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
    zIndex: 10,
  };

  const messagesContainerStyle = {
    flex: 1,
    padding: '16px',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  };

  const messageRowStyle = (sent) => ({
    display: 'flex',
    justifyContent: sent ? 'flex-end' : 'flex-start',
    marginBottom: '4px',
  });

  const messageBubbleStyle = (sent) => ({
    backgroundColor: sent ? '#16a34a' : '#374151',
    color: 'white',
    padding: '8px 12px',
    borderRadius: '8px',
    maxWidth: '300px',
    wordWrap: 'break-word',
    boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
  });

  const messageTextStyle = {
    fontSize: '14px',
    margin: 0,
    lineHeight: '1.4',
  };

  const timestampStyle = (sent) => ({
    fontSize: '11px',
    color: sent ? 'rgba(255,255,255,0.7)' : 'rgba(255,255,255,0.6)',
    marginTop: '4px',
    display: 'block',
  });

  return (
    <Box style={{ flexGrow: 1 }}>
      <div style={containerStyle}>
        <div style={chatContainerStyle}>
          <div style={messagesContainerStyle}>
            {messages.map((message, index) => (
              <React.Fragment key={index}>
                <div style={messageRowStyle(message.sender_role === 'customer')}>
                  <div style={messageBubbleStyle(message.sender_role === 'customer')}>
                    <div style={messageTextStyle}>
                      {message.text_content}
                    </div>
                    <span style={timestampStyle(message.sender_role === 'customer')}>
                      {message.created_at ? new Date(message.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </span>
                  </div>
                </div>
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>
    </Box>
  )
}

export default Message