import { useCallback, useEffect } from 'react';

import { Box } from '@mui/material';

import s1 from '@/assets/topbar/s1.png';
import s1Selected from '@/assets/topbar/s1Selected.png';
import s2 from '@/assets/topbar/s2.png';
import s2Selected from '@/assets/topbar/s2Selected.png';
import s3 from '@/assets/topbar/s3.png';
import s3Selected from '@/assets/topbar/s3Selected.png';
import s4 from '@/assets/topbar/s4.png';
import s4Selected from '@/assets/topbar/s4Selected.png';
import s5 from '@/assets/topbar/s5.png';
import s5Selected from '@/assets/topbar/s5Selected.png';
import s6 from '@/assets/topbar/s6.png';
import s6Selected from '@/assets/topbar/s6Selected.png';
import s7 from '@/assets/topbar/s7.png';
import s7Selected from '@/assets/topbar/s7Selected.png';
import useDebounce from '@/hooks/useDebounce';
import sevenScreenStore from '@/store/sevenScreenStore';

import MenuItem from './MenuItem';
import styles from './TopbarContent.module.css';

const SCREENS = [
  {
    title: 'Screen 1',
    icon: s1,
    selectedIcon: s1Selected,
  },
  {
    title: 'Screen 2',
    icon: s2,
    selectedIcon: s2Selected,
  },
  {
    title: 'Screen 3',
    icon: s3,
    selectedIcon: s3Selected,
  },
  {
    title: 'Screen 4',
    icon: s4,
    selectedIcon: s4Selected,
  },
  {
    title: 'Screen 5',
    icon: s5,
    selectedIcon: s5Selected,
  },
  {
    title: 'Screen 6',
    icon: s6,
    selectedIcon: s6Selected,
  },
  {
    title: 'Screen 7',
    icon: s7,
    selectedIcon: s7Selected,
  },
];

const TopbarContent = ({ onClose }) => {
  const { settings, setCurrentScreen } = sevenScreenStore();
  const { isHorizontal, currentScreen } = settings;

  const getCurrentScreen = useCallback(() => {
    const x = window.pageXOffset;
    const y = window.pageYOffset;
    const screen = isHorizontal ? Math.round(x / 1920) + 1 : Math.round(y / 1080) + 1;
    setCurrentScreen(screen);
  }, [isHorizontal, setCurrentScreen]);

  const debouncedGetCurrentScreen = useDebounce(getCurrentScreen, 200);

  const scrollToTab = (tab) => {
    window.scroll({
      top: isHorizontal ? 0 : tab * 1080,
      left: isHorizontal ? tab * 1920 : 0,
      behavior: 'smooth',
    });
    onClose?.();
  };

  useEffect(() => {
    window.addEventListener('scroll', debouncedGetCurrentScreen);

    // Initial screen check
    getCurrentScreen();

    return () => {
      window.removeEventListener('scroll', debouncedGetCurrentScreen);
    };
  }, [getCurrentScreen, debouncedGetCurrentScreen]);

  return (
    <Box className={styles.container}>
      <Box className={styles.content}>
        {SCREENS.map((screen, index) => (
          <MenuItem
            key={index}
            screen={screen}
            index={index}
            currentScreen={currentScreen}
            onClick={scrollToTab}
          />
        ))}
      </Box>
    </Box>
  );
};

export default TopbarContent;
