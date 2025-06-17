import React, { useState, useEffect } from 'react';
import { AcademicCapIcon, UserGroupIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface ClassGroup {
  id: number;
  name: string;
  name_he: string;
  student_count: number;
}

const ClassesPage: React.FC = () => {
  const [classes, setClasses] = useState<ClassGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('http://localhost:8005/api/v1/classes');
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }
      
      const data = await response.json();
      setClasses(data.classes || []);
      toast.success(`${data.classes?.length || 0} classes chargées`);
    } catch (error) {
      console.error('Erreur lors du chargement des classes:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue';
      setError(errorMessage);
      toast.error('Erreur lors du chargement des classes');
    } finally {
      setLoading(false);
    }
  };

  const retryFetch = () => {
    fetchClasses();
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Chargement des classes...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">Erreur de chargement</h3>
            <p className="mt-2 text-gray-600">{error}</p>
            <button
              onClick={retryFetch}
              className="mt-4 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              Réessayer
            </button>
          </div>
        </div>
      </div>
    );
  }

  const totalStudents = classes.reduce((sum, classGroup) => sum + classGroup.student_count, 0);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <AcademicCapIcon className="h-8 w-8 mr-3 text-purple-600" />
          Gestion des Classes
        </h1>
        <p className="mt-2 text-gray-600">
          Gérez les classes et groupes d'élèves
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <AcademicCapIcon className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Classes</p>
              <p className="text-2xl font-bold text-gray-900">{classes.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <UserGroupIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Élèves</p>
              <p className="text-2xl font-bold text-gray-900">{totalStudents}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <UserGroupIcon className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Moyenne par Classe</p>
              <p className="text-2xl font-bold text-gray-900">
                {classes.length > 0 ? Math.round(totalStudents / classes.length) : 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Classes List */}
      <div className="bg-white shadow-sm rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Liste des Classes ({classes.length})
          </h3>
        </div>
        
        {classes.length === 0 ? (
          <div className="text-center py-12">
            <AcademicCapIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Aucune classe</h3>
            <p className="mt-1 text-sm text-gray-500">
              Aucune classe n'a été trouvée dans le système.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Classe
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Nom (עברית)
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Effectif
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Statut
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {classes.map((classGroup) => (
                  <tr key={classGroup.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10">
                          <div className="h-10 w-10 rounded-full bg-purple-100 flex items-center justify-center">
                            <AcademicCapIcon className="h-6 w-6 text-purple-600" />
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {classGroup.name}
                          </div>
                          <div className="text-sm text-gray-500">
                            ID: {classGroup.id}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900" dir="rtl">
                        {classGroup.name_he}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <UserGroupIcon className="h-4 w-4 text-gray-400 mr-2" />
                        <span className="text-sm font-medium text-gray-900">
                          {classGroup.student_count} élèves
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                        Active
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClassesPage; 