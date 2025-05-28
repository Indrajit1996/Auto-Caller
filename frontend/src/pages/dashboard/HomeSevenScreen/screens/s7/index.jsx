import { Box } from '@mui/material';

import SevenScreenHeader from '@/components/SevenScreenHeader';

import styles from '../Screen.module.css';

const S7 = () => {
  return (
    <Box className={styles.container}>
      <SevenScreenHeader title='Screen 7' />
      <Box component='main' className={styles.main}>
        Screen 7
      </Box>
    </Box>
  );
};

export default S7;
