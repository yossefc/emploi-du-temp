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
  LanguageIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ArrowUpTrayIcon,
} from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

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

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'w-64' : 'w-16'
        } transition-all duration-300 bg-white shadow-lg flex flex-col`}
      >
        {/* Logo/Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {sidebarOpen && (
              <h1 className="text-xl font-bold text-gray-900">
                Emploi du Temps
              </h1>
            )}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-md hover:bg-gray-100 transition-colors"
            >
              {sidebarOpen ? (
                <ChevronLeftIcon className="h-5 w-5 text-gray-600" />
              ) : (
                <ChevronRightIcon className="h-5 w-5 text-gray-600" />
              )}
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center px-3 py-2 text-left rounded-md transition-colors ${
                  window.location.pathname === item.path
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                {sidebarOpen && (
                  <span className="ml-3 font-medium">{item.text}</span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 rounded-md hover:bg-gray-100 transition-colors"
              >
                {sidebarOpen ? (
                  <XMarkIcon className="h-6 w-6 text-gray-600" />
                ) : (
                  <Bars3Icon className="h-6 w-6 text-gray-600" />
                )}
              </button>
              <h2 className="text-lg font-semibold text-gray-900">
                Générateur d'Emploi du Temps
              </h2>
            </div>

            <div className="flex items-center space-x-4">
              {/* Language selector */}
              <button className="p-2 rounded-md hover:bg-gray-100 transition-colors">
                <LanguageIcon className="h-5 w-5 text-gray-600" />
              </button>
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