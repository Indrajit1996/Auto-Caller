import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import SwapVertIcon from '@mui/icons-material/SwapVert';
import { Box, IconButton, Typography } from '@mui/material';

import UserProfileDropdown from '@/components/UserProfileDropdown';
import sevenScreenStore from '@/store/sevenScreenStore';

import styles from './SevenScreenHeader.module.css';

const SevenScreenHeader = ({ title, isFirstScreen = false }) => {
  const { settings, setIsHorizontal } = sevenScreenStore();

  const toggleOrientation = () => {
    setIsHorizontal(!settings.isHorizontal);
  };

  return (
    <header className={styles.header}>
      <Typography className={styles.title}>{title}</Typography>
      {isFirstScreen && (
        <Box className={styles.actionBox}>
          <UserProfileDropdown />
          <IconButton onClick={toggleOrientation} className={styles.iconButton}>
            {settings.isHorizontal ? (
              <SwapVertIcon fontSize='large' />
            ) : (
              <SwapHorizIcon fontSize='large' />
            )}
          </IconButton>
        </Box>
      )}
    </header>
  );
};

export default SevenScreenHeader;
