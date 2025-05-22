import DashboardIcon from '@mui/icons-material/Dashboard';
import GroupAddIcon from '@mui/icons-material/GroupAdd';
import GroupsIcon from '@mui/icons-material/Groups';
import PersonIcon from '@mui/icons-material/Person';

import { ROUTES } from '@/constants/routeConstants';

export const SIDEBAR_ROUTES = [
  {
    routes: [
      {
        path: ROUTES.LOGGED_IN_HOME,
        title: 'Dashboard',
        icon: <DashboardIcon />,
        onlySuperUser: false,
      },
    ],
  },
  {
    section: 'Admin',
    onlySuperUser: true,
    routes: [
      {
        path: ROUTES.ADMIN.USERS,
        title: 'Users',
        icon: <PersonIcon />,
        onlySuperUser: true,
      },
      {
        path: ROUTES.ADMIN.INVITES,
        title: 'Invitations',
        icon: <GroupAddIcon />,
        onlySuperUser: true,
      },
      {
        path: ROUTES.ADMIN.GROUPS,
        title: 'Groups',
        icon: <GroupsIcon />,
        onlySuperUser: true,
      },
    ],
  },
];
