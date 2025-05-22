import { Box } from '@mui/material';

import SevenScreenHeader from '@/components/SevenScreenHeader';

import styles from '../Screen.module.css';

const S5 = () => {
  return (
    <Box className={styles.container}>
      <SevenScreenHeader title='Screen 5' />
      <Box component='main' className={styles.main}>
        Screen 5
      </Box>
    </Box>
  );
};

export default S5;
