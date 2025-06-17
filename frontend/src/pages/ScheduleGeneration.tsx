import React, { useState } from 'react';
import { CalendarDaysIcon, PlayIcon, DocumentCheckIcon, ClockIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface GenerationResult {
  message: string;
  status: string;
}

const ScheduleGenerationPage: React.FC = () => {
  const [formData, setFormData] = useState({
    name: `Emploi du temps ${new Date().getFullYear()}`,
    description: 'Génération automatique d\'emploi du temps'
  });

  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    try {
      setIsGenerating(true);
      setError(null);
      setResult(null);

      const response = await fetch('http://localhost:8005/api/v1/schedules/generate', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json' 
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
      toast.success('Génération lancée avec succès !');
    } catch (error) {
      console.error('Erreur lors de la génération:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue';
      setError(errorMessage);
      toast.error('Erreur lors de la génération');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <CalendarDaysIcon className="h-8 w-8 mr-3 text-indigo-600" />
          Génération d'Emploi du Temps
        </h1>
        <p className="mt-2 text-gray-600">
          Créez automatiquement un emploi du temps optimisé
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            Configuration
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nom de l'emploi du temps
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                rows={3}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className={`w-full flex items-center justify-center px-4 py-3 rounded-md text-white font-medium ${
                isGenerating ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'
              }`}
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Génération...
                </>
              ) : (
                <>
                  <PlayIcon className="h-4 w-4 mr-2" />
                  Générer
                </>
              )}
            </button>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
            <DocumentCheckIcon className="h-5 w-5 mr-2" />
            Résultats
          </h2>
          
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {result && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center mb-2">
                <ClockIcon className="h-5 w-5 text-green-500 mr-2" />
                <span className="font-medium text-green-800">
                  {result.status === 'in_progress' ? 'En cours' : 'Terminé'}
                </span>
              </div>
              <p className="text-green-700">{result.message}</p>
            </div>
          )}

          {!result && !error && (
            <div className="text-center py-12">
              <CalendarDaysIcon className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-gray-500">Lancez une génération</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScheduleGenerationPage; 