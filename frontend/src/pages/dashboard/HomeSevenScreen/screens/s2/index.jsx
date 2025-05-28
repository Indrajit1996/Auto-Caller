import { Box } from '@mui/material';

import SevenScreenHeader from '@/components/SevenScreenHeader';

import styles from '../Screen.module.css';

const S2 = () => {
  return (
    <Box className={styles.container}>
      <SevenScreenHeader title='Screen 2' />
      <Box component='main' className={styles.main}>
        Screen 2
      </Box>
    </Box>
  );
};

export default S2;
