import React from 'react';
import {
  UserGroupIcon,
  AcademicCapIcon,
  BuildingOffice2Icon,
  CalendarDaysIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { useAppSelector } from '../store/hooks';
import Layout from '../components/Common/Layout';

interface StatCard {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
}

const Dashboard: React.FC = () => {
  const { user } = useAppSelector(state => state.auth);
  const { currentSchedule } = useAppSelector(state => state.schedule);

  // Mock schedules data for stats
  const mockSchedules = currentSchedule ? [currentSchedule] : [];

  // Stats simulées - à remplacer par des vraies données
  const stats: StatCard[] = [
    {
      title: 'Enseignants',
      value: 45,
      icon: <UserGroupIcon className="h-6 w-6" />,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      title: 'Classes',
      value: 24,
      icon: <AcademicCapIcon className="h-6 w-6" />,
      color: 'text-green-600',
      bgColor: 'bg-green-100'
    },
    {
      title: 'Salles',
      value: 30,
      icon: <BuildingOffice2Icon className="h-6 w-6" />,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100'
    },
    {
      title: 'Emplois du temps',
      value: mockSchedules.length,
      icon: <CalendarDaysIcon className="h-6 w-6" />,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100'
    }
  ];

  const recentSchedules = mockSchedules.slice(0, 5);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'generated':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Tableau de bord</h1>
          <p className="text-gray-600 mt-1">Bienvenue, {user?.username} !</p>
        </div>

        {/* Cartes de statistiques */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <div key={index} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className={`flex-shrink-0 ${stat.bgColor} ${stat.color} p-3 rounded-lg`}>
                  {stat.icon}
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Emplois du temps récents */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Emplois du temps récents</h2>
            </div>
            <div className="p-6">
              {recentSchedules.length === 0 ? (
                <div className="text-center py-8">
                  <CalendarDaysIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">Aucun emploi du temps généré</p>
                  <p className="text-sm text-gray-400 mt-1">
                    Créez votre premier emploi du temps pour commencer
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {recentSchedules.map((schedule) => (
                    <div
                      key={schedule.id}
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div>
                        <h3 className="font-medium text-gray-900">{schedule.name}</h3>
                        <p className="text-sm text-gray-500">
                          Créé le {new Date().toLocaleDateString('fr-FR')}
                        </p>
                      </div>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(schedule.status)}`}>
                        {schedule.status === 'approved' ? 'Approuvé' :
                         schedule.status === 'generated' ? 'Généré' : 'Brouillon'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Statut du système */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Statut du système</h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div className="flex items-center">
                  <CheckCircleIcon className="h-5 w-5 text-green-500 mr-3" />
                  <span className="text-sm text-gray-700">Base de données : Connectée</span>
                </div>
                
                <div className="flex items-center">
                  <CheckCircleIcon className="h-5 w-5 text-green-500 mr-3" />
                  <span className="text-sm text-gray-700">Solver OR-Tools : Prêt</span>
                </div>
                
                <div className="flex items-center">
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mr-3" />
                  <span className="text-sm text-gray-700">Agent IA : Configuration requise</span>
                </div>
                
                <div className="flex items-center">
                  <CheckCircleIcon className="h-5 w-5 text-green-500 mr-3" />
                  <span className="text-sm text-gray-700">API : En ligne</span>
                </div>
              </div>
              
              <div className="mt-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Utilisation mémoire</span>
                  <span className="text-sm text-gray-500">35%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: '35%' }}></div>
                </div>
                <p className="text-xs text-gray-500 mt-1">2.1 GB / 6 GB</p>
              </div>
            </div>
          </div>
        </div>

        {/* Actions rapides */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Actions rapides</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <CalendarDaysIcon className="h-8 w-8 text-blue-600 mr-3" />
              <div className="text-left">
                <p className="font-medium text-gray-900">Générer un emploi du temps</p>
                <p className="text-sm text-gray-500">Créer un nouvel emploi du temps</p>
              </div>
            </button>
            
            <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <UserGroupIcon className="h-8 w-8 text-green-600 mr-3" />
              <div className="text-left">
                <p className="font-medium text-gray-900">Gérer les enseignants</p>
                <p className="text-sm text-gray-500">Ajouter ou modifier des enseignants</p>
              </div>
            </button>
            
            <button className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <AcademicCapIcon className="h-8 w-8 text-purple-600 mr-3" />
              <div className="text-left">
                <p className="font-medium text-gray-900">Gérer les classes</p>
                <p className="text-sm text-gray-500">Configurer les classes et matières</p>
              </div>
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard; 