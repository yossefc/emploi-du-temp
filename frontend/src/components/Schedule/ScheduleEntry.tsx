import React from 'react';
import { UserIcon, BuildingOfficeIcon } from '@heroicons/react/24/outline';

interface ScheduleEntryProps {
  subject: string;
  teacher: string;
  room: string;
  startTime: string;
  endTime: string;
  type?: 'lecture' | 'lab' | 'exam';
  color?: string;
}

const ScheduleEntry: React.FC<ScheduleEntryProps> = ({
  subject,
  teacher,
  room,
  startTime,
  endTime,
  type = 'lecture',
  color = 'blue'
}) => {
  const getTypeColor = () => {
    switch (type) {
      case 'lecture': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'lab': return 'bg-green-100 text-green-800 border-green-200';
      case 'exam': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getTypeLabel = () => {
    switch (type) {
      case 'lecture': return 'Cours';
      case 'lab': return 'TP';
      case 'exam': return 'Examen';
      default: return 'Autre';
    }
  };

  return (
    <div className={`p-3 rounded-lg border ${getTypeColor()} hover:shadow-md transition-shadow`}>
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="font-semibold text-sm truncate flex-1">{subject}</h4>
          <span className="text-xs px-2 py-1 rounded-full bg-white bg-opacity-60">
            {getTypeLabel()}
          </span>
        </div>
        
        <div className="text-xs space-y-1">
          <div className="flex items-center gap-1">
            <UserIcon className="w-3 h-3" />
            <span className="truncate">{teacher}</span>
          </div>
          
          <div className="flex items-center gap-1">
            <BuildingOfficeIcon className="w-3 h-3" />
            <span className="truncate">{room}</span>
          </div>
        </div>
        
        <div className="text-xs font-medium opacity-75">
          {startTime} - {endTime}
        </div>
      </div>
    </div>
  );
};

export default ScheduleEntry; 