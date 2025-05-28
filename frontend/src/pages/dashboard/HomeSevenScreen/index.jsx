import { Box } from '@mui/material';

import Topbar from '@/components/Topbar';
import sevenScreenStore from '@/store/sevenScreenStore';

import styles from './SevenScreen.module.css';
import { S1, S2, S3, S4, S5, S6, S7 } from './screens';

const DashboardSevenScreen = () => {
  const { settings } = sevenScreenStore();
  const { isHorizontal } = settings;

  return (
    <Box className={isHorizontal ? styles.containerHorizontal : styles.containerVertical}>
      <Topbar />
      {[S1, S2, S3, S4, S5, S6, S7].map((Screen, index) => (
        <div key={index} className={isHorizontal ? styles.screenHorizontal : styles.screenVertical}>
          <Screen />
        </div>
      ))}
    </Box>
  );
};

export default DashboardSevenScreen;
