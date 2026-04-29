import React, { useEffect, useState } from 'react';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface ScheduleGridProps {
  schedule?: any;
  onUpdate?: (updatedSchedule: any) => void;
  readOnly?: boolean;
}

const DAYS = [
  { id: 'sunday', name: 'Dimanche', nameHe: 'ראשון', short: 'Dim' },
  { id: 'monday', name: 'Lundi', nameHe: 'שני', short: 'Lun' },
  { id: 'tuesday', name: 'Mardi', nameHe: 'שלישי', short: 'Mar' },
  { id: 'wednesday', name: 'Mercredi', nameHe: 'רביעי', short: 'Mer' },
  { id: 'thursday', name: 'Jeudi', nameHe: 'חמישי', short: 'Jeu' },
  { id: 'friday', name: 'Vendredi', nameHe: 'שישי', short: 'Ven' },
];

const PERIODS = [
  { id: 1, start: '08:00', end: '08:45' },
  { id: 2, start: '08:50', end: '09:35' },
  { id: 3, start: '09:40', end: '10:25' },
  { id: 4, start: '10:40', end: '11:25' },
  { id: 5, start: '11:30', end: '12:15' },
  { id: 6, start: '12:20', end: '13:05' },
  { id: 7, start: '13:10', end: '13:55' },
  { id: 8, start: '14:00', end: '14:45' },
];

const MOBILE_BREAKPOINT = 768;

const ScheduleGrid: React.FC<ScheduleGridProps> = ({ schedule }) => {
  const [entries] = useState(schedule?.entries || {});
  const [isMobile, setIsMobile] = useState<boolean>(
    typeof window !== 'undefined' ? window.innerWidth < MOBILE_BREAKPOINT : false
  );
  const [activeDayIndex, setActiveDayIndex] = useState<number>(0);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const cellKey = (dayId: string, periodId: number) => `${dayId}-${periodId}`;

  const isUnavailable = (dayId: string, periodId: number) =>
    dayId === 'friday' && periodId > 6;

  const renderEntries = (dayId: string, periodId: number) => {
    const list = entries[cellKey(dayId, periodId)] || [];
    if (list.length === 0) {
      return <span className="text-xs text-gray-400">—</span>;
    }
    return list.map((entry: any, index: number) => (
      <div
        key={entry.id || index}
        className="p-2 bg-blue-100 rounded text-xs sm:text-sm leading-snug"
      >
        <div className="font-medium text-blue-900 truncate">
          {entry.subject || 'Cours'}
        </div>
        <div className="text-blue-700 truncate">
          {entry.teacher || 'Enseignant'}
        </div>
      </div>
    ));
  };

  if (isMobile) {
    const day = DAYS[activeDayIndex];
    const goPrev = () =>
      setActiveDayIndex((i) => (i - 1 + DAYS.length) % DAYS.length);
    const goNext = () => setActiveDayIndex((i) => (i + 1) % DAYS.length);

    return (
      <div className="bg-white rounded-lg shadow-md flex flex-col">
        <div className="flex items-center justify-between p-3 border-b border-gray-200 sticky top-0 bg-white z-10">
          <button
            onClick={goPrev}
            className="p-2 min-h-[44px] min-w-[44px] rounded-md hover:bg-gray-100"
            aria-label="Jour précédent"
          >
            <ChevronLeftIcon className="h-5 w-5 text-gray-600" />
          </button>
          <div className="text-center">
            <div className="text-base font-semibold text-gray-900">
              {day.name}
            </div>
            <div className="text-xs text-gray-500">{day.nameHe}</div>
          </div>
          <button
            onClick={goNext}
            className="p-2 min-h-[44px] min-w-[44px] rounded-md hover:bg-gray-100"
            aria-label="Jour suivant"
          >
            <ChevronRightIcon className="h-5 w-5 text-gray-600" />
          </button>
        </div>

        <div className="flex gap-1 px-2 pt-2 overflow-x-auto">
          {DAYS.map((d, i) => (
            <button
              key={d.id}
              onClick={() => setActiveDayIndex(i)}
              className={`px-3 py-2 rounded-md text-sm font-medium whitespace-nowrap min-h-[40px] ${
                i === activeDayIndex
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700'
              }`}
            >
              {d.short}
            </button>
          ))}
        </div>

        <ul className="divide-y divide-gray-200 p-2">
          {PERIODS.map((period) => {
            const unavailable = isUnavailable(day.id, period.id);
            return (
              <li key={period.id} className="py-3 flex gap-3">
                <div className="w-20 flex-shrink-0">
                  <div className="text-sm font-medium text-gray-900">
                    P{period.id}
                  </div>
                  <div className="text-xs text-gray-500">
                    {period.start}–{period.end}
                  </div>
                </div>
                <div className="flex-1 min-w-0 space-y-1">
                  {unavailable ? (
                    <span className="text-xs text-gray-500">Non disponible</span>
                  ) : (
                    renderEntries(day.id, period.id)
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md max-h-[80vh] overflow-auto">
      <table className="w-full">
        <thead className="bg-gray-50 sticky top-0">
          <tr>
            <th className="font-bold min-w-[100px] p-3 text-left border-b border-gray-200">
              Période
            </th>
            {DAYS.map((day) => (
              <th
                key={day.id}
                className="font-bold text-center p-3 border-b border-gray-200"
              >
                <div className="text-sm font-semibold">{day.name}</div>
                <div className="text-xs text-gray-500">{day.nameHe}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {PERIODS.map((period) => (
            <tr key={period.id}>
              <td className="font-medium p-3 border-b border-gray-200">
                <div className="text-sm">Période {period.id}</div>
                <div className="text-xs text-gray-500">
                  {period.start} - {period.end}
                </div>
              </td>
              {DAYS.map((day) => {
                if (isUnavailable(day.id, period.id)) {
                  return (
                    <td
                      key={`${day.id}-${period.id}`}
                      className="bg-gray-100 relative p-2 min-h-[80px]"
                    >
                      <span className="text-sm text-gray-500">
                        Non disponible
                      </span>
                    </td>
                  );
                }
                return (
                  <td
                    key={`${day.id}-${period.id}`}
                    className="relative min-h-[80px] p-2 border border-gray-200 align-top"
                  >
                    <div className="space-y-1">
                      {renderEntries(day.id, period.id)}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ScheduleGrid;
