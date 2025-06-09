import React, { useState } from 'react';

interface ScheduleGridProps {
  schedule?: any;
  onUpdate?: (updatedSchedule: any) => void;
  readOnly?: boolean;
}

const DAYS = [
  { id: 'sunday', name: 'Dimanche', nameHe: 'ראשון' },
  { id: 'monday', name: 'Lundi', nameHe: 'שני' },
  { id: 'tuesday', name: 'Mardi', nameHe: 'שלישי' },
  { id: 'wednesday', name: 'Mercredi', nameHe: 'רביעי' },
  { id: 'thursday', name: 'Jeudi', nameHe: 'חמישי' },
  { id: 'friday', name: 'Vendredi', nameHe: 'שישי' }
];

const PERIODS = [
  { id: 1, start: '08:00', end: '08:45' },
  { id: 2, start: '08:50', end: '09:35' },
  { id: 3, start: '09:40', end: '10:25' },
  { id: 4, start: '10:40', end: '11:25' },
  { id: 5, start: '11:30', end: '12:15' },
  { id: 6, start: '12:20', end: '13:05' },
  { id: 7, start: '13:10', end: '13:55' },
  { id: 8, start: '14:00', end: '14:45' }
];

const ScheduleGrid: React.FC<ScheduleGridProps> = ({ schedule, onUpdate, readOnly = false }) => {
  const [entries, setEntries] = useState(schedule?.entries || {});

  const getCellKey = (dayId: string, periodId: number) => `${dayId}-${periodId}`;

  const renderCell = (dayId: string, periodId: number) => {
    const cellKey = getCellKey(dayId, periodId);
    const cellEntries = entries[cellKey] || [];
    
    // Vendredi après 13h - cellule grisée
    if (dayId === 'friday' && periodId > 6) {
      return (
        <td className="bg-gray-100 relative p-2 min-h-[80px]">
          <span className="text-sm text-gray-500">
            Non disponible
          </span>
        </td>
      );
    }

    return (
      <td className="relative min-h-[80px] p-2 border border-gray-200">
        <div className="min-h-[60px] rounded p-1">
          {cellEntries.map((entry: any, index: number) => (
            <div key={entry.id || index} className="mb-1">
              <div className="p-2 bg-blue-100 rounded text-xs">
                {entry.subject || 'Cours'} - {entry.teacher || 'Enseignant'}
              </div>
            </div>
          ))}
        </div>
      </td>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-md max-h-[80vh] overflow-auto">
      <table className="w-full">
        <thead className="bg-gray-50 sticky top-0">
          <tr>
            <th className="font-bold min-w-[100px] p-3 text-left border-b border-gray-200">
              Période
            </th>
            {DAYS.map(day => (
              <th key={day.id} className="font-bold text-center p-3 border-b border-gray-200">
                <div>
                  <div className="text-sm font-semibold">{day.name}</div>
                  <div className="text-xs text-gray-500">
                    {day.nameHe}
                  </div>
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {PERIODS.map(period => (
            <tr key={period.id}>
              <td className="font-medium p-3 border-b border-gray-200">
                <div>
                  <div className="text-sm">Période {period.id}</div>
                  <div className="text-xs text-gray-500">
                    {period.start} - {period.end}
                  </div>
                </div>
              </td>
              {DAYS.map(day => (
                <React.Fragment key={`${day.id}-${period.id}`}>
                  {renderCell(day.id, period.id)}
                </React.Fragment>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ScheduleGrid; 