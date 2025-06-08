import React, { useState } from 'react';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  CssBaseline,
  useTheme,
  Avatar,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  Dashboard,
  CalendarMonth,
  People,
  School,
  MeetingRoom,
  Settings,
  Build,
  Logout,
  Language,
  Person,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { logout } from '../../store/slices/authSlice';

const drawerWidth = 240;

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [open, setOpen] = useState(true);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [langAnchorEl, setLangAnchorEl] = useState<null | HTMLElement>(null);
  
  const user = useAppSelector(state => state.auth.user);

  const handleDrawerToggle = () => {
    setOpen(!open);
  };

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLanguageMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setLangAnchorEl(event.currentTarget);
  };

  const handleLanguageMenuClose = () => {
    setLangAnchorEl(null);
  };

  const handleLogout = async () => {
    await dispatch(logout());
    navigate('/login');
  };

  const menuItems = [
    { text: 'Tableau de bord', icon: <Dashboard />, path: '/dashboard' },
    { text: 'Emploi du temps', icon: <CalendarMonth />, path: '/schedule' },
    { text: 'Enseignants', icon: <People />, path: '/teachers' },
    { text: 'Matières', icon: <School />, path: '/subjects' },
    { text: 'Classes', icon: <School />, path: '/classes' },
    { text: 'Salles', icon: <MeetingRoom />, path: '/rooms' },
    { text: 'Contraintes', icon: <Build />, path: '/constraints' },
  ];

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: `calc(100% - ${open ? drawerWidth : theme.spacing(7)}px)`,
          ml: `${open ? drawerWidth : theme.spacing(7)}px`,
          transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="toggle drawer"
            onClick={handleDrawerToggle}
            edge="start"
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Générateur d'Emplois du Temps
          </Typography>
          
          <IconButton color="inherit" onClick={handleLanguageMenuOpen}>
            <Language />
          </IconButton>
          
          <IconButton onClick={handleProfileMenuOpen} sx={{ ml: 2 }}>
            <Avatar sx={{ width: 32, height: 32 }}>
              {user?.username?.charAt(0).toUpperCase()}
            </Avatar>
          </IconButton>
        </Toolbar>
      </AppBar>

      <Drawer
        sx={{
          width: open ? drawerWidth : theme.spacing(7),
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: open ? drawerWidth : theme.spacing(7),
            boxSizing: 'border-box',
            transition: theme.transitions.create('width', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
            overflowX: 'hidden',
          },
        }}
        variant="permanent"
        anchor="left"
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: open ? 'flex-end' : 'center',
            padding: theme.spacing(0, 1),
            ...theme.mixins.toolbar,
          }}
        >
          <IconButton onClick={handleDrawerToggle}>
            {theme.direction === 'ltr' ? (
              open ? <ChevronLeftIcon /> : <ChevronRightIcon />
            ) : (
              open ? <ChevronRightIcon /> : <ChevronLeftIcon />
            )}
          </IconButton>
        </Box>
        <Divider />
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding sx={{ display: 'block' }}>
              <ListItemButton
                sx={{
                  minHeight: 48,
                  justifyContent: open ? 'initial' : 'center',
                  px: 2.5,
                }}
                onClick={() => navigate(item.path)}
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
                <ListItemText primary={item.text} sx={{ opacity: open ? 1 : 0 }} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
        <Divider />
        <List>
          <ListItem disablePadding sx={{ display: 'block' }}>
            <ListItemButton
              sx={{
                minHeight: 48,
                justifyContent: open ? 'initial' : 'center',
                px: 2.5,
              }}
              onClick={() => navigate('/settings')}
            >
              <ListItemIcon
                sx={{
                  minWidth: 0,
                  mr: open ? 3 : 'auto',
                  justifyContent: 'center',
                }}
              >
                <Settings />
              </ListItemIcon>
              <ListItemText primary="Paramètres" sx={{ opacity: open ? 1 : 0 }} />
            </ListItemButton>
          </ListItem>
        </List>
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: 'background.default',
          p: 3,
          width: `calc(100% - ${open ? drawerWidth : theme.spacing(7)}px)`,
          ml: `${open ? drawerWidth : theme.spacing(7)}px`,
          transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Toolbar />
        {children}
      </Box>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleProfileMenuClose}
      >
        <MenuItem onClick={() => navigate('/profile')}>
          <ListItemIcon>
            <Person />
          </ListItemIcon>
          Profil
        </MenuItem>
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <Logout />
          </ListItemIcon>
          Déconnexion
        </MenuItem>
      </Menu>

      <Menu
        anchorEl={langAnchorEl}
        open={Boolean(langAnchorEl)}
        onClose={handleLanguageMenuClose}
      >
        <MenuItem onClick={() => {
          // TODO: Implement language change
          handleLanguageMenuClose();
        }}>
          Français
        </MenuItem>
        <MenuItem onClick={() => {
          // TODO: Implement language change
          handleLanguageMenuClose();
        }}>
          עברית
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default Layout; 