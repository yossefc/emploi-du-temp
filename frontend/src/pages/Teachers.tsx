import React, { useState, useEffect } from 'react';
import { UserIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import apiService from '../services/api';

interface Teacher {
  id: number;
  code: string;
  first_name: string;
  last_name: string;
  email: string;
  subjects: Array<{ name_fr?: string; name_he?: string; code: string }>;
}

interface Subject {
  id: number;
  code: string;
  name_fr: string;
  name_he: string;
}

// Données de test basées sur ce qui est dans la base de données
const TEST_TEACHERS = [
  {
    id: 1,
    code: "PROF001",
    first_name: "Jean",
    last_name: "Dupont",
    email: "jean.dupont@school.com",
    subjects: [{ name_fr: "Mathématiques", code: "MATH" }]
  },
  {
    id: 2,
    code: "PROF002", 
    first_name: "Sarah",
    last_name: "Cohen",
    email: "sarah.cohen@school.com",
    subjects: [{ name_fr: "Français", code: "FR" }]
  },
  {
    id: 3,
    code: "PROF003",
    first_name: "David",
    last_name: "Levy",
    email: "david.levy@school.com", 
    subjects: [{ name_fr: "Sciences", code: "SCI" }]
  },
  {
    id: 4,
    code: "PROF004",
    first_name: "Rachel",
    last_name: "Martin",
    email: "rachel.martin@school.com",
    subjects: [{ name_fr: "Histoire", code: "HIST" }]
  },
  {
    id: 5,
    code: "PROF005",
    first_name: "Michel",
    last_name: "Bernard",
    email: "michel.bernard@school.com",
    subjects: [{ name_fr: "Géographie", code: "GEO" }]
  }
];

const TeachersPage: React.FC = () => {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [useTestData, setUseTestData] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTeacher, setNewTeacher] = useState({
    code: '',
    first_name: '',
    last_name: '',
    email: '',
    subject_ids: [] as number[]
  });

  useEffect(() => {
    fetchTeachers();
    fetchSubjects();
  }, []);

  const fetchTeachers = async () => {
    try {
      // Essayer d'abord l'API réelle
      const response = await apiService.getTeachers();
      console.log('Response from API:', response.data);
      setTeachers(response.data || []);
      setUseTestData(false);
    } catch (error) {
      console.error('Error fetching teachers:', error);
      console.log('🔄 API non disponible, utilisation des données de test...');
      
      // Si l'API échoue, utiliser les données de test
      setTeachers(TEST_TEACHERS);
      setUseTestData(true);
      toast.error('API non disponible - Données de test affichées');
    } finally {
      setLoading(false);
    }
  };

  const fetchSubjects = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/subjects-test');
      const data = await response.json();
      setSubjects(data || []);
    } catch (error) {
      console.error('Error fetching subjects:', error);
      // Données de test pour les matières
      setSubjects([
        { id: 1, code: 'MATH', name_fr: 'Mathématiques', name_he: 'מתמטיקה' },
        { id: 2, code: 'FR', name_fr: 'Français', name_he: 'צרפתית' },
        { id: 3, code: 'SCI', name_fr: 'Sciences', name_he: 'מדעים' },
        { id: 4, code: 'HIST', name_fr: 'Histoire', name_he: 'היסטוריה' },
        { id: 5, code: 'GEO', name_fr: 'Géographie', name_he: 'גיאוגרפיה' }
      ]);
    }
  };

  const handleAddTeacher = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newTeacher.first_name || !newTeacher.last_name || !newTeacher.code) {
      toast.error('Veuillez remplir tous les champs obligatoires');
      return;
    }

    try {
      if (useTestData) {
        // Simulation d'ajout pour les données de test
        const mockTeacher: Teacher = {
          id: Math.max(...teachers.map(t => t.id)) + 1,
          code: newTeacher.code,
          first_name: newTeacher.first_name,
          last_name: newTeacher.last_name,
          email: newTeacher.email,
          subjects: subjects.filter(s => newTeacher.subject_ids.includes(s.id))
        };
        
        setTeachers([...teachers, mockTeacher]);
        toast.success('Enseignant ajouté (mode test)');
      } else {
        // Utiliser l'API réelle
        const response = await apiService.createTeacher(newTeacher);
        await fetchTeachers(); // Recharger la liste
        toast.success('Enseignant ajouté avec succès');
      }
      
      // Reset form
      setNewTeacher({
        code: '',
        first_name: '',
        last_name: '',
        email: '',
        subject_ids: []
      });
      setShowAddForm(false);
      
    } catch (error) {
      console.error('Error adding teacher:', error);
      toast.error('Erreur lors de l\'ajout de l\'enseignant');
    }
  };

  const handleSubjectChange = (subjectId: number, checked: boolean) => {
    if (checked) {
      setNewTeacher({
        ...newTeacher,
        subject_ids: [...newTeacher.subject_ids, subjectId]
      });
    } else {
      setNewTeacher({
        ...newTeacher,
        subject_ids: newTeacher.subject_ids.filter(id => id !== subjectId)
      });
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <UserIcon className="h-8 w-8 mr-3 text-blue-600" />
            Gestion des Enseignants
          </h1>
          <button
            onClick={() => setShowAddForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center hover:bg-blue-700 transition-colors"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Ajouter un enseignant
          </button>
        </div>
        
        {useTestData && (
          <div className="mt-4 p-3 bg-yellow-100 border border-yellow-400 rounded-md">
            <p className="text-yellow-800 text-sm">
              ⚠️ Mode test - Le backend n'est pas accessible. Les modifications ne seront pas sauvegardées.
            </p>
          </div>
        )}
      </div>

      {/* Formulaire d'ajout */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Ajouter un enseignant</h2>
              <button
                onClick={() => setShowAddForm(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            
            <form onSubmit={handleAddTeacher} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Code enseignant *
                </label>
                <input
                  type="text"
                  value={newTeacher.code}
                  onChange={(e) => setNewTeacher({...newTeacher, code: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Ex: PROF006"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Prénom *
                </label>
                <input
                  type="text"
                  value={newTeacher.first_name}
                  onChange={(e) => setNewTeacher({...newTeacher, first_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nom de famille *
                </label>
                <input
                  type="text"
                  value={newTeacher.last_name}
                  onChange={(e) => setNewTeacher({...newTeacher, last_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={newTeacher.email}
                  onChange={(e) => setNewTeacher({...newTeacher, email: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Matières enseignées
                </label>
                <div className="max-h-32 overflow-y-auto space-y-2">
                  {subjects.map((subject) => (
                    <label key={subject.id} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={newTeacher.subject_ids.includes(subject.id)}
                        onChange={(e) => handleSubjectChange(subject.id, e.target.checked)}
                        className="mr-2"
                      />
                      <span className="text-sm">{subject.name_fr} ({subject.code})</span>
                    </label>
                  ))}
                </div>
              </div>
              
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Ajouter
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-medium">
              Liste des Enseignants 
              {useTestData ? '(Données de test)' : `(${teachers.length} enseignants)`}
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Code
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Nom
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Matières
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {teachers.map((teacher) => (
                  <tr key={teacher.id} className={useTestData ? 'bg-yellow-50' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {teacher.code}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {teacher.first_name} {teacher.last_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {teacher.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {teacher.subjects?.map(subject => subject.name_fr || subject.code).join(', ') || 'Aucune matière'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {!useTestData && teachers.length === 0 && (
            <div className="px-6 py-4 text-center text-gray-500">
              Aucun enseignant trouvé. Utilisez le bouton "Ajouter un enseignant" pour commencer.
            </div>
          )}
          
          {useTestData && (
            <div className="px-6 py-4 bg-blue-50 border-t">
              <button 
                onClick={fetchTeachers}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                🔄 Réessayer l'API
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TeachersPage; 