import React from 'react';
import { Box, Typography, Paper, List, ListItem, ListItemText } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ConversationSummary from '@/components/ConversationSummary';
import CallButton from '@/components/CallButton';
import useConversationStore from '@/store/conversationStore';
import { ROUTES } from '@/constants/routeConstants';

const sidebarUsers = [
    { id: 1, name: 'Sachin' },
    { id: 2, name: 'Indra' },
];

function getSummaryFromHistory(history) {
    let summary = [];
    history.forEach(item => {
        const userName = sidebarUsers.find(u => u.id === item.userId)?.name || 'Unknown';
        item.conversation.forEach(msg => {
            if (msg.sender === 'user') {
                summary.push({
                    name: userName,
                    question: msg.text,
                    elapsed: msg.simulatedElapsed || null,
                });
            }
        });
    });
    return summary;
}

const DashboardSingleScreen = () => {
    const navigate = useNavigate();
    const { history, restoreFromHistory } = useConversationStore();
    const summary = getSummaryFromHistory(history);

    const handleRestoreChat = (idx) => {
        const restoredUserId = restoreFromHistory(idx);
        if(restoredUserId) {
            navigate(ROUTES.CONVERSATION);
        }
    };

    return (
        <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h5" sx={{ p: 2 }}>Dashboard</Typography>
            
            <Paper sx={{ width: '100%', borderRadius: 0 }}>
                <Typography variant="h6" sx={{ p: 2, borderBottom: '1px solid #eee' }}>Summary of Past Conversations</Typography>
                <ConversationSummary summary={summary} />
            </Paper>

            <Paper sx={{ mt: 2, p: 2 }}>
                <Typography variant="h6" sx={{ mb: 1 }}>Conversation History</Typography>
                {history.length === 0 ? (
                    <Typography color="text.secondary">No closed chats yet.</Typography>
                ) : (
                    <List>
                        {history.map((item, idx) => (
                            <ListItem key={idx} button onClick={() => handleRestoreChat(idx)} alignItems="flex-start">
                                <ListItemText
                                    primary={`Chat with ${sidebarUsers.find(u => u.id === item.userId)?.name || 'User'}`}
                                    secondary={`Closed at: ${item.closedAt.toLocaleString()}`}
                                />
                            </ListItem>
                        ))}
                    </List>
                )}
            </Paper>

            <Paper sx={{ mt: 2, p: 2 }}>
                <Typography variant="h6" sx={{ mb: 1 }}>Make a Call</Typography>
                <CallButton />
            </Paper>
        </Box>
    );
};

export default DashboardSingleScreen;
