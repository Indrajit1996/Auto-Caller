import styled from '@emotion/styled';
import { Box } from '@mui/material';

import Header from '@/components/Header';
import { COLLAPSED_DRAWER_WIDTH, DRAWER_WIDTH } from '@/constants/sidebarConstants';
import { useUserSettings } from '@/hooks';

const MainContentBox = styled(Box, {
  shouldForwardProp: (prop) => !['disableSidebar', 'open'].includes(prop),
})(({ theme, disableSidebar, open }) => ({
  display: 'block',
  position: 'relative',
  marginLeft: disableSidebar ? 0 : `${open ? DRAWER_WIDTH : COLLAPSED_DRAWER_WIDTH}px`,
  transition: theme.transitions.create(['margin', 'width'], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  [theme.breakpoints.down('md')]: {
    marginLeft: 0,
  },
  padding: 0,
  '& > *': {
    padding: 0
  }
}));

export const AppLayout = ({ disableSidebar = false, children }) => {
  const { sidebarCollapsed } = useUserSettings();

  return (
    <>
      <Header disableSidebar={disableSidebar} />
      <MainContentBox component='main' disableSidebar={disableSidebar} open={!sidebarCollapsed}>
        {children}
      </MainContentBox>
    </>
  );
};
