import { useState } from 'react';
import { useEffect } from 'react';

import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import {
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
} from '@mui/material'; 
import { useLocation, useNavigate } from 'react-router';

import { SIDEBAR_ROUTES } from '@/components/Sidebar/SidebarRoutes';
import { Drawer, DrawerHeader } from '@/components/Sidebar/StyledDrawer';
import { useAuth } from '@/hooks';

const generateSidebarItems = (routes, isSuperUser) => {
  const items = [];

  routes.forEach((section) => {
    // Skip admin section if not super user
    if (section.onlySuperUser && !isSuperUser) {
      return;
    }

    // Add section header
    items.push({
      kind: 'header',
      title: section.section,
    });

    // Add routes for this section
    const sectionRoutes = section.routes
      .filter((route) => !route.onlySuperUser || isSuperUser)
      .map((route) => ({
        kind: 'item',
        segment: route.path,
        title: route.title,
        icon: route.icon,
      }));

    items.push(...sectionRoutes);
  });

  return items;
};

export const NavigationDrawer = ({ open, onToggle, drawerWidth, collapsedDrawerWidth }) => {
  const { isSuperUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarItems, setSidebarItems] = useState([]);

  useEffect(() => {
    setSidebarItems(generateSidebarItems(SIDEBAR_ROUTES, isSuperUser));
  }, [isSuperUser]);

  return (
    <Drawer
      variant='permanent'
      open={open}
      drawerWidth={drawerWidth}
      collapsedDrawerWidth={collapsedDrawerWidth}
    >
      <DrawerHeader>
        <IconButton onClick={onToggle}>{open && <ChevronLeftIcon />}</IconButton>
      </DrawerHeader>
      <Divider />
      <List>
        {sidebarItems.map((item) =>
          item.kind === 'header' ? (
            <ListItem
              key={`header-${item.title}`}
              sx={{
                opacity: open ? 1 : 0,
                height: open ? 'auto' : 0,
                transition: 'all 0.2s',
              }}
            >
              <Typography variant='overline' color='text.secondary' fontWeight={600}>
                {item.title}
              </Typography>
            </ListItem>
          ) : (
            <ListItem key={`sidebar-item-${item.title}`} disablePadding>
              <ListItemButton
                sx={{
                  minHeight: 48,
                  justifyContent: open ? 'initial' : 'center',
                  px: 2.5,
                }}
                selected={location.pathname.includes(item.segment)}
                onClick={() => navigate(item.segment)}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 0,
                    mr: open ? 3 : 'auto',
                    justifyContent: 'center',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.title} sx={{ opacity: open ? 1 : 0 }} />
              </ListItemButton>
            </ListItem>
          )
        )}
      </List>
    </Drawer>
  );
};
