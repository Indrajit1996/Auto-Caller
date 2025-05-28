import { Box } from '@mui/material';

import SevenScreenHeader from '@/components/SevenScreenHeader';

import styles from '../Screen.module.css';

const S4 = () => {
  return (
    <Box className={styles.container}>
      <SevenScreenHeader title='Screen 4' />
      <Box component='main' className={styles.main}>
        Screen 4
      </Box>
    </Box>
  );
};

export default S4;
