import React, { useState } from 'react';
import {
  PlusIcon,
  ArrowDownTrayIcon,
  PlayIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { generateSchedule, setCurrentSchedule } from '../store/slices/scheduleSlice';
import Layout from '../components/Common/Layout';
import ScheduleGrid from '../components/Schedule/ScheduleGrid';
import ChatInterface from '../components/AI/ChatInterface';

const SchedulePage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { currentSchedule, isLoading, error } = useAppSelector(state => state.schedule);
  const [openGenerate, setOpenGenerate] = useState(false);
  const [scheduleName, setScheduleName] = useState('');
  const [showChat, setShowChat] = useState(false);

  const handleGenerateSchedule = async () => {
    if (!scheduleName.trim()) return;
    
    try {
      const result = await dispatch(generateSchedule({
        name: scheduleName,
        constraints: [],
        preferences: {}
      }));
      
      if (generateSchedule.fulfilled.match(result)) {
        setOpenGenerate(false);
        setScheduleName('');
      }
    } catch (error) {
      console.error('Schedule generation error:', error);
    }
  };

  const handleExport = (format: 'pdf' | 'excel' | 'ics') => {
    if (currentSchedule) {
      // Mock export - replace with actual API call
      console.log(`Exporting ${currentSchedule.name} as ${format}`);
    }
  };

  const handleAIMessage = async (message: string) => {
    // Mock AI response - replace with actual API call
    return {
      text: "Je suis un assistant IA pour vous aider avec vos emplois du temps. Comment puis-je vous aider ?",
      suggestions: []
    };
  };

  const handleScheduleUpdate = (updatedSchedule: any) => {
    dispatch(setCurrentSchedule(updatedSchedule));
  };

  return (
    <Layout>
      <div className="flex-1 relative">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Emploi du temps
          </h1>
          
          <div className="flex gap-2">
            {currentSchedule && (
              <>
                <button
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  onClick={() => handleExport('excel')}
                >
                  <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                  Excel
                </button>
                <button
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  onClick={() => handleExport('pdf')}
                >
                  <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                  PDF
                </button>
                <button
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  onClick={() => handleExport('ics')}
                >
                  <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                  Calendrier
                </button>
              </>
            )}
            <button
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              onClick={() => setOpenGenerate(true)}
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Générer
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="text-sm text-red-700">
              {error}
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="bg-white shadow rounded-lg p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            <h3 className="mt-4 text-lg font-medium text-gray-900">
              Génération en cours...
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              Cela peut prendre quelques minutes selon la complexité
            </p>
          </div>
        ) : currentSchedule ? (
          <div className={`grid gap-6 ${showChat ? 'grid-cols-1 lg:grid-cols-3' : 'grid-cols-1'}`}>
            <div className={showChat ? 'lg:col-span-2' : 'col-span-1'}>
              <div className="bg-white shadow rounded-lg p-4">
                <div className="mb-4 flex justify-between items-center">
                  <h2 className="text-lg font-medium text-gray-900">
                    {currentSchedule.name}
                  </h2>
                  {currentSchedule.conflicts && currentSchedule.conflicts.length > 0 && (
                    <div className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                      {currentSchedule.conflicts.length} conflit(s) détecté(s)
                    </div>
                  )}
                </div>
                <ScheduleGrid
                  schedule={currentSchedule}
                  onUpdate={handleScheduleUpdate}
                  readOnly={false}
                />
              </div>
            </div>
            
            {showChat && (
              <div className="lg:col-span-1">
                <div className="bg-white shadow rounded-lg h-96 lg:h-[80vh] flex flex-col">
                  <ChatInterface
                    onSendMessage={handleAIMessage}
                    language="fr"
                  />
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white shadow rounded-lg p-8 text-center">
            <h3 className="text-lg font-medium text-gray-500">
              Aucun emploi du temps sélectionné
            </h3>
            <p className="mt-2 text-sm text-gray-400">
              Cliquez sur "Générer" pour créer un nouvel emploi du temps
            </p>
          </div>
        )}

        {/* FAB pour ouvrir/fermer le chat */}
        {currentSchedule && (
          <button
            className="fixed bottom-6 right-6 w-14 h-14 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-200"
            onClick={() => setShowChat(!showChat)}
            title={showChat ? "Fermer l'assistant" : "Ouvrir l'assistant IA"}
          >
            <ChatBubbleLeftRightIcon className="w-6 h-6 mx-auto" />
          </button>
        )}

        {/* Dialog de génération */}
        {openGenerate && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setOpenGenerate(false)}></div>
              
              <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
              
              <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                    Générer un nouvel emploi du temps
                  </h3>
                  <input
                    type="text"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="Nom de l'emploi du temps"
                    value={scheduleName}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setScheduleName(e.target.value)}
                    onKeyPress={(e: React.KeyboardEvent) => {
                      if (e.key === 'Enter' && scheduleName.trim()) {
                        handleGenerateSchedule();
                      }
                    }}
                  />
                </div>
                
                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="button"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    onClick={handleGenerateSchedule}
                    disabled={!scheduleName.trim()}
                  >
                    Générer
                  </button>
                  <button
                    type="button"
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                    onClick={() => setOpenGenerate(false)}
                  >
                    Annuler
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default SchedulePage; 