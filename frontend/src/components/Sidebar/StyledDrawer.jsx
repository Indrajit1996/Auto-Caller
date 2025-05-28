import styled from '@emotion/styled';
import MuiDrawer from '@mui/material/Drawer';

export const Drawer = styled(MuiDrawer, {
  shouldForwardProp: (prop) => !['open', 'drawerWidth', 'collapsedDrawerWidth'].includes(prop),
})(({ theme, open, drawerWidth = 240, collapsedDrawerWidth = 65 }) => ({
  width: drawerWidth,
  ...(open && {
    ...openedMixin(theme, drawerWidth),
    '& .MuiDrawer-paper': openedMixin(theme, drawerWidth),
  }),
  ...(!open && {
    ...closedMixin(theme, collapsedDrawerWidth),
    '& .MuiDrawer-paper': closedMixin(theme, collapsedDrawerWidth),
  }),
}));

const openedMixin = (theme, drawerWidth) => ({
  width: drawerWidth,
  transition: theme.transitions.create('width', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.enteringScreen,
  }),
  overflowX: 'hidden',
});

const closedMixin = (theme, collapsedDrawerWidth) => ({
  transition: theme.transitions.create('width', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  overflowX: 'hidden',
  width: collapsedDrawerWidth,
  // if viewport is sm or lower, the drawer will be closed
  [theme.breakpoints.down('md')]: {
    width: 0,
  },
});

export const DrawerHeader = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'flex-end',
  padding: theme.spacing(0, 1),
  ...theme.mixins.toolbar,
}));
