import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  Typography, 
  List, 
  ListItem, 
  ListItemAvatar,
  ListItemText,
  Avatar,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import AddIcon from '@mui/icons-material/Add';

import ConversationView from '@/components/ConversationView';
import useConversationStore from '@/store/conversationStore';
import { ROUTES } from '@/constants/routeConstants';

const sidebarUsers = [
  { id: 1, name: 'Sachin' },
  { id: 2, name: 'Indra' },
];

const ConversationPage = () => {
  const navigate = useNavigate();
  const { 
    conversations, 
    setConversations,
    addHistory,
    clearConversationsForUser 
  } = useConversationStore();

  const [selectedChat, setSelectedChat] = useState(null);

  const handleCloseChat = () => {
    if (selectedChat) {
      const convo = conversations[selectedChat] || [];
      if (convo.length > 0) {
        addHistory({ userId: selectedChat, conversation: convo, closedAt: new Date() });
      }
      clearConversationsForUser(selectedChat);
      setSelectedChat(null);
      navigate(ROUTES.DASHBOARD);
    }
  };

  const handleAddMoreNames = () => {
    // TODO: Implement add more names functionality
    console.log('Add more names clicked');
  };

  return (
    <Box sx={{ width: '100%', display: 'flex', height: '100vh' }}>
      {/* Left sidebar with chat list */}
      <Box sx={{ 
        width: 320, 
        borderRight: '1px solid #e0e0e0',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <Box sx={{ 
          p: 2, 
          borderBottom: '1px solid #e0e0e0',
          bgcolor: '#f5f5f5',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <Typography variant="h6">Chats</Typography>
          <Tooltip title="Add more names">
            <IconButton onClick={handleAddMoreNames} size="small">
              <AddIcon />
            </IconButton>
          </Tooltip>
        </Box>
        
        <List sx={{ width: '100%', bgcolor: 'background.paper', p: 0 }}>
          {sidebarUsers.map((chat, index) => (
            <React.Fragment key={chat.id}>
              <ListItem 
                alignItems="flex-start"
                button
                selected={selectedChat === chat.id}
                onClick={() => setSelectedChat(chat.id)}
                sx={{ 
                  px: 2,
                  py: 1.5,
                  '&:hover': {
                    bgcolor: '#f5f5f5'
                  },
                  '&.Mui-selected': {
                    bgcolor: '#e3f2fd',
                    '&:hover': {
                      bgcolor: '#e3f2fd'
                    }
                  }
                }}
              >
                <ListItemAvatar>
                  <Avatar>{chat.name[0]}</Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography component="span" variant="subtitle1" color="text.primary">
                        {chat.name}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
              {index < sidebarUsers.length - 1 && <Divider component="li" />}
            </React.Fragment>
          ))}
        </List>
      </Box>

      {/* Right side chat view */}
      {selectedChat ? (
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ 
            p: 2, 
            borderBottom: '1px solid #e0e0e0',
            bgcolor: '#f5f5f5',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Avatar sx={{ mr: 1 }}>{sidebarUsers.find(c => c.id === selectedChat)?.name[0]}</Avatar>
              <Typography variant="h6">
                {sidebarUsers.find(c => c.id === selectedChat)?.name}
              </Typography>
            </Box>
            <Button 
              color="error" 
              variant="outlined" 
              size="small" 
              onClick={handleCloseChat}
            >
              Close & Archive Chat
            </Button>
          </Box>
          <ConversationView
            selectedUser={selectedChat}
            conversations={conversations}
            setConversations={setConversations}
            sidebarUsers={sidebarUsers}
            onSummaryUpdate={() => {}}
          />
        </Box>
      ) : (
        <Box 
          sx={{ 
            flex: 1, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            bgcolor: '#f5f5f5'
          }}
        >
          <Typography variant="h6" color="text.secondary">
            Select a chat to start messaging
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default ConversationPage; 