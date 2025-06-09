import React, { useState } from 'react';
import { Transition } from '@headlessui/react';
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
  ArrowRightOnRectangleIcon,
  LanguageIcon,
  UserIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';
import { Menu } from '@headlessui/react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { logout } from '../../store/slices/authSlice';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  const user = useAppSelector(state => state.auth.user);

  const handleLogout = async () => {
    await dispatch(logout());
    navigate('/login');
  };

  const menuItems = [
    { text: 'Tableau de bord', icon: HomeIcon, path: '/dashboard' },
    { text: 'Emploi du temps', icon: CalendarDaysIcon, path: '/schedule' },
    { text: 'Enseignants', icon: UserGroupIcon, path: '/teachers' },
    { text: 'Matières', icon: AcademicCapIcon, path: '/subjects' },
    { text: 'Classes', icon: AcademicCapIcon, path: '/classes' },
    { text: 'Salles', icon: BuildingOffice2Icon, path: '/rooms' },
    { text: 'Contraintes', icon: WrenchScrewdriverIcon, path: '/constraints' },
  ];

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className={`bg-white shadow-lg transition-all duration-300 ${sidebarOpen ? 'w-64' : 'w-16'}`}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          {sidebarOpen && (
            <h1 className="text-lg font-semibold text-gray-900">
              Générateur EDT
            </h1>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1 rounded-md hover:bg-gray-100 transition-colors"
          >
            {sidebarOpen ? (
              <ChevronLeftIcon className="h-5 w-5 text-gray-600" />
            ) : (
              <ChevronRightIcon className="h-5 w-5 text-gray-600" />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="mt-4">
          <ul className="space-y-1 px-2">
            {menuItems.map((item) => (
              <li key={item.text}>
                <button
                  onClick={() => navigate(item.path)}
                  className={`
                    w-full flex items-center px-3 py-2 text-sm font-medium rounded-md
                    text-gray-700 hover:bg-gray-100 hover:text-gray-900
                    transition-colors duration-200
                    ${!sidebarOpen ? 'justify-center' : ''}
                  `}
                  title={!sidebarOpen ? item.text : undefined}
                >
                  <item.icon className={`h-5 w-5 ${sidebarOpen ? 'mr-3' : ''}`} />
                  {sidebarOpen && <span>{item.text}</span>}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* Settings */}
        <div className="absolute bottom-0 w-full border-t border-gray-200 p-2">
          <button
            onClick={() => navigate('/settings')}
            className={`
              w-full flex items-center px-3 py-2 text-sm font-medium rounded-md
              text-gray-700 hover:bg-gray-100 hover:text-gray-900
              transition-colors duration-200
              ${!sidebarOpen ? 'justify-center' : ''}
            `}
            title={!sidebarOpen ? 'Paramètres' : undefined}
          >
            <CogIcon className={`h-5 w-5 ${sidebarOpen ? 'mr-3' : ''}`} />
            {sidebarOpen && <span>Paramètres</span>}
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden p-2 rounded-md hover:bg-gray-100"
              >
                <Bars3Icon className="h-6 w-6 text-gray-600" />
              </button>
              <h2 className="text-xl font-semibold text-gray-900 ml-2">
                Générateur d'Emplois du Temps
              </h2>
            </div>

            <div className="flex items-center space-x-4">
              {/* Language selector */}
              <Menu as="div" className="relative">
                <Menu.Button className="p-2 rounded-md hover:bg-gray-100 transition-colors">
                  <LanguageIcon className="h-5 w-5 text-gray-600" />
                </Menu.Button>
                <Transition
                  enter="transition ease-out duration-100"
                  enterFrom="transform opacity-0 scale-95"
                  enterTo="transform opacity-100 scale-100"
                  leave="transition ease-in duration-75"
                  leaveFrom="transform opacity-100 scale-100"
                  leaveTo="transform opacity-0 scale-95"
                >
                  <Menu.Items className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                    <div className="py-1">
                      <Menu.Item>
                        {({ active }) => (
                          <button
                            className={`${
                              active ? 'bg-gray-100' : ''
                            } block px-4 py-2 text-sm text-gray-700 w-full text-left`}
                          >
                            Français
                          </button>
                        )}
                      </Menu.Item>
                      <Menu.Item>
                        {({ active }) => (
                          <button
                            className={`${
                              active ? 'bg-gray-100' : ''
                            } block px-4 py-2 text-sm text-gray-700 w-full text-left`}
                          >
                            עברית
                          </button>
                        )}
                      </Menu.Item>
                    </div>
                  </Menu.Items>
                </Transition>
              </Menu>

              {/* User menu */}
              <Menu as="div" className="relative">
                <Menu.Button className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-100 transition-colors">
                  <div className="h-8 w-8 bg-blue-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">
                      {user?.username?.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <span className="text-sm font-medium text-gray-700">{user?.username}</span>
                </Menu.Button>
                <Transition
                  enter="transition ease-out duration-100"
                  enterFrom="transform opacity-0 scale-95"
                  enterTo="transform opacity-100 scale-100"
                  leave="transition ease-in duration-75"
                  leaveFrom="transform opacity-100 scale-100"
                  leaveTo="transform opacity-0 scale-95"
                >
                  <Menu.Items className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                    <div className="py-1">
                      <Menu.Item>
                        {({ active }) => (
                          <button
                            onClick={() => navigate('/profile')}
                            className={`${
                              active ? 'bg-gray-100' : ''
                            } flex items-center px-4 py-2 text-sm text-gray-700 w-full text-left`}
                          >
                            <UserIcon className="h-4 w-4 mr-2" />
                            Mon profil
                          </button>
                        )}
                      </Menu.Item>
                      <Menu.Item>
                        {({ active }) => (
                          <button
                            onClick={() => navigate('/settings')}
                            className={`${
                              active ? 'bg-gray-100' : ''
                            } flex items-center px-4 py-2 text-sm text-gray-700 w-full text-left`}
                          >
                            <CogIcon className="h-4 w-4 mr-2" />
                            Paramètres
                          </button>
                        )}
                      </Menu.Item>
                      <div className="border-t border-gray-100">
                        <Menu.Item>
                          {({ active }) => (
                            <button
                              onClick={handleLogout}
                              className={`${
                                active ? 'bg-gray-100' : ''
                              } flex items-center px-4 py-2 text-sm text-gray-700 w-full text-left`}
                            >
                              <ArrowRightOnRectangleIcon className="h-4 w-4 mr-2" />
                              Déconnexion
                            </button>
                          )}
                        </Menu.Item>
                      </div>
                    </div>
                  </Menu.Items>
                </Transition>
              </Menu>
            </div>
          </div>
        </header>

        {/* Main content area */}
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout; 