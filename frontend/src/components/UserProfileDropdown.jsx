import { useState } from 'react';

import { Group, Logout, Mail, Person } from '@mui/icons-material';
import {
  Avatar,
  Box,
  Divider,
  IconButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Typography,
} from '@mui/material';
import { useNavigate } from 'react-router';

import { ROUTES } from '@/constants/routeConstants';
import useAuth from '@/hooks/useAuth';

const getMenuItems = (isSuperUser) => {
  const baseMenuItems = [
    {
      id: 'profile',
      label: 'Profile',
      icon: Person,
      onClick: () => {},
      divider: false,
    },
    {
      id: 'logout',
      label: 'Logout',
      icon: Logout,
      onClick: (logout) => logout(),
      divider: false,
    },
  ];

  const superUserMenuItems = isSuperUser
    ? [
        {
          id: 'users',
          label: 'Users',
          icon: Group,
          onClick: () => {},
          divider: false,
        },
        {
          id: 'invites',
          label: 'Invites',
          icon: Mail,
          onClick: () => {},
          divider: false,
        },
        {
          id: 'groups',
          label: 'Groups',
          icon: Group,
          onClick: () => {},
          divider: true,
        },
      ]
    : [];

  return [...superUserMenuItems, ...baseMenuItems];
};

const UserProfileDropdown = () => {
  const [anchorEl, setAnchorEl] = useState(null);
  const { user, logout, isSuperUser } = useAuth();
  const open = Boolean(anchorEl);

  const navigate = useNavigate();

  const menuItems = getMenuItems(isSuperUser);

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleMenuItemClick = (id) => {
    switch (id) {
      case 'profile':
        navigate(ROUTES.PROFILE);
        break;
      case 'users':
        navigate(ROUTES.ADMIN.USERS);
        break;
      case 'invites':
        navigate(ROUTES.ADMIN.INVITES);
        break;
      case 'groups':
        navigate(ROUTES.ADMIN.GROUPS);
        break;
      case 'logout':
        logout();
        break;
    }
  };

  // Get initials from user's name or use fallback
  const getInitials = () => {
    if (!user?.first_name && !user?.last_name) return '?';
    const firstInitial = user.first_name ? user.first_name[0] : '';
    const lastInitial = user.last_name ? user.last_name[0] : '';
    return (firstInitial + lastInitial).toUpperCase();
  };

  return (
    <>
      <IconButton
        onClick={handleClick}
        size='small'
        aria-controls={open ? 'profile-menu' : undefined}
        aria-haspopup='true'
        aria-expanded={open ? 'true' : undefined}
      >
        <Avatar
          sx={{
            width: { xs: 32, sm: 36, md: 40 },
            height: { xs: 32, sm: 36, md: 40 },
            bgcolor: 'primary.main',
            cursor: 'pointer',
            '&:hover': {
              opacity: 0.9,
            },
          }}
        >
          {getInitials()}
        </Avatar>
      </IconButton>

      <Menu
        id='profile-menu'
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        onClick={handleClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        slotProps={{
          elevation: {
            elevation: 0,
            sx: {
              overflow: 'visible',
              filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
              mt: 1.5,
              width: 220,
              '& .MuiAvatar-root': {
                width: 32,
                height: 32,
                ml: -0.5,
                mr: 1,
              },
            },
          },
        }}
      >
        <MenuItem sx={{ py: 1 }}>
          <Box>
            <Typography
              variant='subtitle1'
              noWrap
              sx={{
                maxWidth: { xs: 120, sm: 150, md: 200 },
                fontWeight: 500,
              }}
            >
              {user ? `${user.first_name} ${user.last_name}` : 'User'}
            </Typography>
            <Typography
              variant='body2'
              color='textSecondary'
              noWrap
              sx={{
                maxWidth: { xs: 120, sm: 150, md: 200 },
                fontSize: '0.75rem',
              }}
            >
              {user?.email}
            </Typography>
          </Box>
        </MenuItem>

        <Divider />

        {menuItems.map((item) => (
          <div key={item.id}>
            <MenuItem onClick={() => handleMenuItemClick(item.id)}>
              <ListItemIcon>
                <item.icon fontSize='small' />
              </ListItemIcon>
              <ListItemText>{item.label}</ListItemText>
            </MenuItem>
            {item.divider && <Divider />}
          </div>
        ))}
      </Menu>
    </>
  );
};

export default UserProfileDropdown;
