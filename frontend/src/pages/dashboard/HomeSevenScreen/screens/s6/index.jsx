import { Box } from '@mui/material';

import SevenScreenHeader from '@/components/SevenScreenHeader';

import styles from '../Screen.module.css';

const S6 = () => {
  return (
    <Box className={styles.container}>
      <SevenScreenHeader title='Screen 6' />
      <Box component='main' className={styles.main}>
        Screen 6
      </Box>
    </Box>
  );
};

export default S6;
