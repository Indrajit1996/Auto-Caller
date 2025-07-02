import { Box } from '@mui/material';
import SevenScreenHeader from '@/components/SevenScreenHeader';
import ConversationSummary from '@/components/ConversationSummary';
import styles from '../Screen.module.css';

const S1 = () => {
  return (
    <Box className={styles.container}>
      <SevenScreenHeader title='Screen 1' isFirstScreen={true} />
      <Box component='main' className={styles.main} sx={{ p: 0 }}>
        <ConversationSummary />
      </Box>
    </Box>
  );
};

export default S1;
