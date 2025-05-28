// Header.jsx
import styled from '@emotion/styled';
import MenuIcon from '@mui/icons-material/Menu';
import MenuOpenIcon from '@mui/icons-material/MenuOpen';
import {
  Grid2 as Grid,
  IconButton,
  LinearProgress,
  AppBar as MuiAppBar,
  Toolbar,
  Typography,
} from '@mui/material';
import { Link } from 'react-router';

import NotificationPanel from '@/components/NotificationPanel';
import { NavigationDrawer } from '@/components/Sidebar/Drawer';
import UserProfileDropdown from '@/components/UserProfileDropdown';
import { ROUTES } from '@/constants/routeConstants';
import { COLLAPSED_DRAWER_WIDTH, DRAWER_WIDTH } from '@/constants/sidebarConstants';
import { useAuth, useUserSettings } from '@/hooks';

const AppBar = styled(MuiAppBar)(({ theme }) => ({
  backgroundColor: theme.palette.background.paper,
  zIndex: theme.zIndex.drawer + 1,
  transition: theme.transitions.create(['width', 'margin'], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
}));

const Header = ({ disableSidebar = false }) => {
  const appName = import.meta.env.VITE_APP_NAME || 'Project Name';
  const { sidebarCollapsed, setSidebarCollapsed } = useUserSettings();
  const { isLoading } = useAuth();

  const handleDrawerToggle = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  return (
    <div style={{ position: 'relative' }}>
      <AppBar
        color='inherit'
        position='fixed'
        elevation={0}
        sx={{
          borderBottom: 1,
          borderBottomColor: 'divider',
          borderBottomStyle: 'solid',
        }}
        open={!sidebarCollapsed}
      >
        <Toolbar>
          <IconButton
            color='inherit'
            aria-label='open drawer'
            onClick={handleDrawerToggle}
            edge='start'
            sx={{
              marginRight: 2,
            }}
          >
            {!disableSidebar && (sidebarCollapsed ? <MenuIcon /> : <MenuOpenIcon />)}
          </IconButton>
          <Typography
            variant='h6'
            color='inherit'
            noWrap
            sx={{
              flexGrow: 1,
              fontWeight: 600,
              letterSpacing: -0.5,
              textDecoration: 'none',
              color: 'inherit',
            }}
            component={Link}
            to={ROUTES.LOGGED_IN_HOME}
          >
            {appName}
          </Typography>
          <Grid container spacing={2} alignItems='center'>
            <NotificationPanel />
            <UserProfileDropdown />
          </Grid>
        </Toolbar>
      </AppBar>
      {!disableSidebar && (
        <NavigationDrawer
          open={!sidebarCollapsed}
          onToggle={handleDrawerToggle}
          drawerWidth={DRAWER_WIDTH}
          collapsedDrawerWidth={COLLAPSED_DRAWER_WIDTH}
        />
      )}
      <Toolbar />
      {isLoading && <LinearProgress />}
    </div>
  );
};

export default Header;
