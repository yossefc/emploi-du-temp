import React, { useState, useEffect } from 'react';
import { BuildingOffice2Icon, MapPinIcon, ExclamationTriangleIcon, ComputerDesktopIcon, BeakerIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface Room {
  id: number;
  name: string;
  capacity: number;
  type: string;
}

const RoomsPage: React.FC = () => {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRooms();
  }, []);

  const fetchRooms = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('http://localhost:8005/api/v1/rooms');
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }
      
      const data = await response.json();
      setRooms(data.rooms || []);
      toast.success(`${data.rooms?.length || 0} salles chargées`);
    } catch (error) {
      console.error('Erreur lors du chargement des salles:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue';
      setError(errorMessage);
      toast.error('Erreur lors du chargement des salles');
    } finally {
      setLoading(false);
    }
  };

  const retryFetch = () => {
    fetchRooms();
  };

  const getRoomTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'laboratory':
        return <BeakerIcon className="h-6 w-6 text-green-600" />;
      case 'computer':
        return <ComputerDesktopIcon className="h-6 w-6 text-blue-600" />;
      default:
        return <BuildingOffice2Icon className="h-6 w-6 text-gray-600" />;
    }
  };

  const getRoomTypeLabel = (type: string) => {
    switch (type.toLowerCase()) {
      case 'laboratory':
        return 'Laboratoire';
      case 'computer':
        return 'Informatique';
      case 'classroom':
        return 'Salle de classe';
      default:
        return type;
    }
  };

  const getRoomTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'laboratory':
        return 'bg-green-100 text-green-800';
      case 'computer':
        return 'bg-blue-100 text-blue-800';
      case 'classroom':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Chargement des salles...</p>
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
              className="mt-4 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              Réessayer
            </button>
          </div>
        </div>
      </div>
    );
  }

  const totalCapacity = rooms.reduce((sum, room) => sum + room.capacity, 0);
  const roomTypes = [...new Set(rooms.map(room => room.type))];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center">
          <BuildingOffice2Icon className="h-8 w-8 mr-3 text-indigo-600" />
          Gestion des Salles
        </h1>
        <p className="mt-2 text-gray-600">
          Gérez les salles et espaces pédagogiques
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-indigo-100 rounded-lg">
              <BuildingOffice2Icon className="h-6 w-6 text-indigo-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Salles</p>
              <p className="text-2xl font-bold text-gray-900">{rooms.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <MapPinIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Capacité Totale</p>
              <p className="text-2xl font-bold text-gray-900">{totalCapacity}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <BeakerIcon className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Types de Salles</p>
              <p className="text-2xl font-bold text-gray-900">{roomTypes.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <MapPinIcon className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Capacité Moyenne</p>
              <p className="text-2xl font-bold text-gray-900">
                {rooms.length > 0 ? Math.round(totalCapacity / rooms.length) : 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Room Types Summary */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Types de Salles</h3>
        <div className="flex flex-wrap gap-2">
          {roomTypes.map((type) => {
            const count = rooms.filter(room => room.type === type).length;
            return (
              <span
                key={type}
                className={`px-3 py-1 text-sm font-medium rounded-full ${getRoomTypeColor(type)}`}
              >
                {getRoomTypeLabel(type)} ({count})
              </span>
            );
          })}
        </div>
      </div>

      {/* Rooms List */}
      <div className="bg-white shadow-sm rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Liste des Salles ({rooms.length})
          </h3>
        </div>
        
        {rooms.length === 0 ? (
          <div className="text-center py-12">
            <BuildingOffice2Icon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Aucune salle</h3>
            <p className="mt-1 text-sm text-gray-500">
              Aucune salle n'a été trouvée dans le système.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Salle
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Capacité
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Statut
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {rooms.map((room) => (
                  <tr key={room.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10">
                          <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                            {getRoomTypeIcon(room.type)}
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {room.name}
                          </div>
                          <div className="text-sm text-gray-500">
                            ID: {room.id}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRoomTypeColor(room.type)}`}>
                        {getRoomTypeLabel(room.type)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <MapPinIcon className="h-4 w-4 text-gray-400 mr-2" />
                        <span className="text-sm font-medium text-gray-900">
                          {room.capacity} places
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                        Disponible
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

export default RoomsPage; 