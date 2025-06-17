import React, { useState, useEffect } from 'react';
import { BookOpenIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface Subject {
  id: number;
  name: string;
  name_he: string;
  code: string;
}

const SubjectsPage: React.FC = () => {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSubjects();
  }, []);

  const fetchSubjects = async () => {
    try {
      const response = await fetch('http://localhost:8005/api/v1/subjects');
      const data = await response.json();
      setSubjects(data.subjects || []);
    } catch (error) {
      toast.error('Erreur lors du chargement des matières');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <BookOpenIcon className="h-8 w-8 mr-3 text-green-600" />
          Gestion des Matières
        </h1>
      </div>

      {loading ? (
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-green-600"></div>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-medium">Liste des Matières ({subjects.length})</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Code
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Nom (Français)
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Nom (עברית)
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {subjects.map((subject) => (
                  <tr key={subject.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                        {subject.code}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {subject.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500" dir="rtl">
                      {subject.name_he}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default SubjectsPage; 