import React, { useState } from 'react';
import { ArrowUpTrayIcon, DocumentCheckIcon, ExclamationTriangleIcon, InformationCircleIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface ImportResult {
  import: Array<{
    json: any;
    sql_insert: string;
  }>;
  errors: string[];
  summary: {
    total_rows: number;
    successful_imports: number;
    errors_count: number;
  };
}

const ImportDataPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFileSelect = (selectedFile: File) => {
    const allowedTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
      'application/vnd.ms-excel', // .xls
      'text/csv' // .csv
    ];

    if (!allowedTypes.includes(selectedFile.type)) {
      toast.error('Format de fichier non supporté. Utilisez .xlsx, .xls ou .csv');
      return;
    }

    setFile(selectedFile);
    setResult(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const handleImport = async () => {
    if (!file) return;

    setImporting(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8005/api/v1/import/import-teachers', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erreur lors de l\'importation');
      }

      const data: ImportResult = await response.json();
      setResult(data);

      if (data.summary.successful_imports > 0) {
        toast.success(`${data.summary.successful_imports} enseignants importés avec succès`);
      }
      if (data.summary.errors_count > 0) {
        toast.error(`${data.summary.errors_count} erreurs détectées`);
      }
    } catch (error) {
      console.error('Erreur d\'importation:', error);
      toast.error(error instanceof Error ? error.message : 'Erreur lors de l\'importation');
    } finally {
      setImporting(false);
    }
  };

  const downloadTemplate = () => {
    const headers = [
      'prenom',
      'nom', 
      'classe',
      'type_classe',
      'matiere',
      'sous_matiere',
      'heures_par_semaine',
      'disponibilites',
      'contraintes_speciales'
    ];
    
    const sampleData = [
      'Jean,Dupont,6e1,classe,Mathématiques,Algèbre,4,"Lundi matin; Mercredi après-midi","Pas de vendredi après-midi"',
      'Marie,Martin,י1,promotion,Français,Littérature,3,"Mardi matin; Jeudi matin","Max 6h par jour"'
    ];

    const csvContent = [headers.join(','), ...sampleData].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = 'template_enseignants.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <ArrowUpTrayIcon className="h-8 w-8 mr-3 text-blue-600" />
          Importation des Enseignants
        </h1>
        <p className="mt-2 text-gray-600">
          Importez les données des enseignants à partir d'un fichier Excel ou CSV
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Sélectionner un fichier
            </h2>
            
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragOver 
                  ? 'border-blue-400 bg-blue-50' 
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              <ArrowUpTrayIcon className="mx-auto h-12 w-12 text-gray-400" />
              <div className="mt-4">
                <label htmlFor="file-upload" className="cursor-pointer">
                  <span className="mt-2 block text-sm font-medium text-gray-900">
                    Glissez un fichier ici ou cliquez pour sélectionner
                  </span>
                  <input
                    id="file-upload"
                    name="file-upload"
                    type="file"
                    className="sr-only"
                    accept=".xlsx,.xls,.csv"
                    onChange={handleFileInputChange}
                  />
                </label>
                <p className="mt-1 text-xs text-gray-500">
                  Formats supportés: .xlsx, .xls, .csv (max 10MB)
                </p>
              </div>
            </div>

            {file && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <DocumentCheckIcon className="h-5 w-5 text-green-500 mr-2" />
                  <span className="text-sm font-medium text-gray-900">
                    {file.name}
                  </span>
                  <span className="ml-2 text-xs text-gray-500">
                    ({(file.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
              </div>
            )}

            <div className="mt-6 flex space-x-3">
              <button
                onClick={handleImport}
                disabled={!file || importing}
                className={`flex-1 px-4 py-2 rounded-md text-sm font-medium ${
                  file && !importing
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                {importing ? 'Importation...' : 'Importer'}
              </button>
              
              <button
                onClick={downloadTemplate}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Télécharger le modèle
              </button>
            </div>
          </div>

          <div className="bg-blue-50 rounded-lg p-6">
            <div className="flex">
              <InformationCircleIcon className="h-5 w-5 text-blue-400 mr-2 mt-0.5" />
              <div>
                <h3 className="text-sm font-medium text-blue-800">Format du fichier</h3>
                <div className="mt-2 text-sm text-blue-700">
                  <p>Colonnes requises :</p>
                  <ul className="list-disc list-inside mt-1 space-y-1">
                    <li><strong>prenom</strong> : Prénom de l'enseignant</li>
                    <li><strong>nom</strong> : Nom de l'enseignant</li>
                    <li><strong>classe</strong> : Classe (ex: "6e1", "י1")</li>
                    <li><strong>matiere</strong> : Matière enseignée</li>
                    <li><strong>heures_par_semaine</strong> : Nombre d'heures</li>
                  </ul>
                  <p className="mt-2">Colonnes optionnelles :</p>
                  <ul className="list-disc list-inside mt-1 space-y-1">
                    <li><strong>type_classe</strong> : "classe" ou "promotion"</li>
                    <li><strong>sous_matiere</strong> : Spécialisation</li>
                    <li><strong>disponibilites</strong> : Créneaux (séparés par ";")</li>
                    <li><strong>contraintes_speciales</strong> : Contraintes (séparées par ";")</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div>
          {result && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Résultats de l'importation
              </h2>

              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="text-center p-3 bg-gray-50 rounded">
                  <div className="text-2xl font-bold text-gray-900">
                    {result.summary.total_rows}
                  </div>
                  <div className="text-sm text-gray-500">Total lignes</div>
                </div>
                <div className="text-center p-3 bg-green-50 rounded">
                  <div className="text-2xl font-bold text-green-600">
                    {result.summary.successful_imports}
                  </div>
                  <div className="text-sm text-gray-500">Succès</div>
                </div>
                <div className="text-center p-3 bg-red-50 rounded">
                  <div className="text-2xl font-bold text-red-600">
                    {result.summary.errors_count}
                  </div>
                  <div className="text-sm text-gray-500">Erreurs</div>
                </div>
              </div>

              {result.errors.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-red-800 mb-2 flex items-center">
                    <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                    Erreurs détectées
                  </h3>
                  <div className="bg-red-50 border border-red-200 rounded p-3 max-h-40 overflow-y-auto">
                    {result.errors.map((error, index) => (
                      <div key={index} className="text-sm text-red-700">
                        {error}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.import.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-2">
                    Aperçu des données importées ({result.import.length} premiers)
                  </h3>
                  <div className="max-h-60 overflow-y-auto border border-gray-200 rounded">
                    {result.import.slice(0, 5).map((item, index) => (
                      <div key={index} className="p-3 border-b border-gray-100 last:border-b-0">
                        <div className="text-sm font-medium text-gray-900">
                          {item.json.prenom} {item.json.nom}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {item.json.matiere} - {item.json.classes[0].promotion} - {item.json.heures_par_semaine}h/semaine
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ImportDataPage; 