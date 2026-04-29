import React, { useEffect, useState } from 'react';
import {
  Bars3Icon,
  XMarkIcon,
  HomeIcon,
  CalendarDaysIcon,
  UserGroupIcon,
  AcademicCapIcon,
  BuildingOffice2Icon,
  CogIcon,
  WrenchScrewdriverIcon,
  LanguageIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ArrowUpTrayIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAppDispatch } from '../../store/hooks';
import { logout } from '../../store/slices/authSlice';

interface LayoutProps {
  children: React.ReactNode;
}

const MOBILE_BREAKPOINT = 1024;

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();

  const handleLogout = async () => {
    await dispatch(logout());
    navigate('/login', { replace: true });
  };

  const [isMobile, setIsMobile] = useState<boolean>(
    typeof window !== 'undefined' ? window.innerWidth < MOBILE_BREAKPOINT : false
  );
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false);
  const [desktopCollapsed, setDesktopCollapsed] = useState<boolean>(false);

  useEffect(() => {
    const onResize = () => {
      const mobile = window.innerWidth < MOBILE_BREAKPOINT;
      setIsMobile(mobile);
      if (!mobile) setDrawerOpen(false);
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    if (isMobile) setDrawerOpen(false);
  }, [location.pathname, isMobile]);

  const menuItems = [
    { text: 'Tableau de bord', icon: HomeIcon, path: '/dashboard' },
    { text: 'Emploi du temps', icon: CalendarDaysIcon, path: '/schedule' },
    { text: 'Enseignants', icon: UserGroupIcon, path: '/teachers' },
    { text: 'Matières', icon: AcademicCapIcon, path: '/subjects' },
    { text: 'Classes', icon: AcademicCapIcon, path: '/classes' },
    { text: 'Salles', icon: BuildingOffice2Icon, path: '/rooms' },
    { text: 'Importation', icon: ArrowUpTrayIcon, path: '/import' },
    { text: 'Contraintes', icon: WrenchScrewdriverIcon, path: '/constraints' },
    { text: 'Paramètres', icon: CogIcon, path: '/settings' },
  ];

  const showLabels = isMobile ? true : !desktopCollapsed;

  const sidebarWidthClass = isMobile
    ? 'w-72'
    : desktopCollapsed
    ? 'w-16'
    : 'w-64';

  const sidebarPositionClass = isMobile
    ? `fixed inset-y-0 left-0 z-40 transform transition-transform duration-300 ${
        drawerOpen ? 'translate-x-0' : '-translate-x-full'
      }`
    : 'relative transition-all duration-300';

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden">
      {isMobile && drawerOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40"
          onClick={() => setDrawerOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        className={`${sidebarPositionClass} ${sidebarWidthClass} bg-white shadow-lg flex flex-col`}
      >
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {showLabels && (
              <h1 className="text-lg sm:text-xl font-bold text-gray-900 truncate">
                Emploi du Temps
              </h1>
            )}
            {isMobile ? (
              <button
                onClick={() => setDrawerOpen(false)}
                className="p-2 rounded-md hover:bg-gray-100 transition-colors"
                aria-label="Fermer le menu"
              >
                <XMarkIcon className="h-6 w-6 text-gray-600" />
              </button>
            ) : (
              <button
                onClick={() => setDesktopCollapsed((v) => !v)}
                className="p-2 rounded-md hover:bg-gray-100 transition-colors"
                aria-label={desktopCollapsed ? 'Ouvrir le menu' : 'Réduire le menu'}
              >
                {desktopCollapsed ? (
                  <ChevronRightIcon className="h-5 w-5 text-gray-600" />
                ) : (
                  <ChevronLeftIcon className="h-5 w-5 text-gray-600" />
                )}
              </button>
            )}
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const active = location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center px-3 min-h-[44px] text-left rounded-md transition-colors ${
                  active ? 'bg-blue-100 text-blue-700' : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                {showLabels && (
                  <span className="ml-3 font-medium text-base">{item.text}</span>
                )}
              </button>
            );
          })}
        </nav>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <header className="bg-white shadow-sm border-b border-gray-200 px-3 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center space-x-3 min-w-0">
              {isMobile && (
                <button
                  onClick={() => setDrawerOpen(true)}
                  className="p-2 -ml-2 rounded-md hover:bg-gray-100 transition-colors"
                  aria-label="Ouvrir le menu"
                >
                  <Bars3Icon className="h-6 w-6 text-gray-600" />
                </button>
              )}
              <h2 className="text-base sm:text-lg font-semibold text-gray-900 truncate">
                Générateur d'Emploi du Temps
              </h2>
            </div>

            <div className="flex items-center gap-1">
              <button
                className="p-2 rounded-md hover:bg-gray-100 transition-colors"
                aria-label="Changer de langue"
              >
                <LanguageIcon className="h-5 w-5 text-gray-600" />
              </button>
              <button
                onClick={handleLogout}
                className="p-2 rounded-md hover:bg-gray-100 transition-colors"
                aria-label="Se déconnecter"
                title="Se déconnecter"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5 text-gray-600" />
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto bg-gray-50 p-3 sm:p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
