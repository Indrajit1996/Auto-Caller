import { useState } from 'react';

import CloseIcon from '@mui/icons-material/Close';
import MenuIcon from '@mui/icons-material/Menu';
import { Box, Drawer, IconButton } from '@mui/material';

import styles from './Topbar.module.css';
import TopbarContent from './TopbarContent';

const Topbar = () => {
  const [showTopbar, setShowTopbar] = useState(false);

  const toggleTopbar = () => {
    setShowTopbar(!showTopbar);
  };

  return (
    <Box className={styles.container}>
      <IconButton
        edge='start'
        color='inherit'
        aria-label='menu'
        onClick={toggleTopbar}
        className={styles.menuButton}
      >
        {showTopbar ? (
          <CloseIcon className={styles.menuIcon} />
        ) : (
          <MenuIcon className={styles.menuIcon} />
        )}
      </IconButton>
      <Drawer anchor='top' open={showTopbar} onClose={toggleTopbar}>
        <TopbarContent onClose={toggleTopbar} />
      </Drawer>
    </Box>
  );
};

export default Topbar;
