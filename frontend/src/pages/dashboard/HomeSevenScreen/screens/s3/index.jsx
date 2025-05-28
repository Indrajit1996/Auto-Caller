import { Box } from '@mui/material';

import SevenScreenHeader from '@/components/SevenScreenHeader';

import styles from '../Screen.module.css';

const S3 = () => {
  return (
    <Box className={styles.container}>
      <SevenScreenHeader title='Screen 3' />
      <Box component='main' className={styles.main}>
        Screen 3
      </Box>
    </Box>
  );
};

export default S3;
