import '../index.css';
import { Box } from '@mui/material';

const Conversation = ({ conversation, handleClick }) => {
  return (
    <Box className="conversation-item" onClick={handleClick}>
      {/* Avatar */}
      <Box className="conversation-avatar">
        {conversation.customer_id?.[0]?.toUpperCase() || '?'}
      </Box>

      {/* Text content */}
      <Box className="conversation-text">
        <Box className="conversation-title">
          Conversation #{conversation.id.slice(0, 8)}
        </Box>
        <Box className="conversation-subtitle">
          {conversation.customer_id.slice(0, 8)}
        </Box>
      </Box>
    </Box>
  );
};

export default Conversation;