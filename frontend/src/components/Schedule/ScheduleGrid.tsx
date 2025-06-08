import React, { useState } from 'react';
import { 
  Box, 
  Paper, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Typography
} from '@mui/material';

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

const ScheduleGrid: React.FC<ScheduleGridProps> = ({ schedule, onUpdate: _onUpdate, readOnly: _readOnly = false }) => {
  const [entries] = useState(schedule?.entries || {});

  const getCellKey = (dayId: string, periodId: number) => `${dayId}-${periodId}`;

  const renderCell = (dayId: string, periodId: number) => {
    const cellKey = getCellKey(dayId, periodId);
    const cellEntries = entries[cellKey] || [];
    
    // Vendredi après 13h - cellule grisée
    if (dayId === 'friday' && periodId > 6) {
      return (
        <TableCell sx={{ backgroundColor: '#f5f5f5', position: 'relative' }}>
          <Typography variant="caption" color="text.secondary">
            Non disponible
          </Typography>
        </TableCell>
      );
    }

    return (
      <TableCell sx={{ position: 'relative', minHeight: 80, p: 1 }}>
        <Box
          sx={{
            minHeight: 60,
            borderRadius: 1,
            p: 0.5
          }}
        >
          {cellEntries.map((entry: any, index: number) => (
            <Box key={entry.id || index} sx={{ mb: 0.5 }}>
              {/* Temporairement remplacé par un simple affichage */}
              <Box
                sx={{
                  p: 1,
                  backgroundColor: '#e3f2fd',
                  borderRadius: 1,
                  fontSize: '0.75rem'
                }}
              >
                {entry.subject || 'Cours'} - {entry.teacher || 'Enseignant'}
              </Box>
            </Box>
          ))}
        </Box>
      </TableCell>
    );
  };

  return (
    <TableContainer component={Paper} sx={{ maxHeight: '80vh' }}>
      <Table stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: 'bold', minWidth: 100 }}>
              Période
            </TableCell>
            {DAYS.map(day => (
              <TableCell key={day.id} align="center" sx={{ fontWeight: 'bold' }}>
                <Box>
                  <Typography variant="subtitle2">{day.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {day.nameHe}
                  </Typography>
                </Box>
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {PERIODS.map(period => (
            <TableRow key={period.id}>
              <TableCell sx={{ fontWeight: 'medium' }}>
                <Box>
                  <Typography variant="body2">Période {period.id}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {period.start} - {period.end}
                  </Typography>
                </Box>
              </TableCell>
              {DAYS.map(day => (
                <React.Fragment key={`${day.id}-${period.id}`}>
                  {renderCell(day.id, period.id)}
                </React.Fragment>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default ScheduleGrid; 