import React from 'react';
import { Box, Chip, Typography, Tooltip } from '@mui/material';
import {  Person, Room } from '@mui/icons-material';

interface ScheduleEntryProps {
  entry: {
    id: string;
    subject: {
      name: string;
      code: string;
      color?: string;
    };
    teacher: {
      firstName: string;
      lastName: string;
      code: string;
    };
    room: {
      name: string;
      code: string;
    };
    classGroup: {
      name: string;
      code: string;
    };
  };
  isDragging?: boolean;
}

const ScheduleEntry: React.FC<ScheduleEntryProps> = ({ entry, isDragging = false }) => {
  const backgroundColor = entry.subject.color || '#2196f3';
  
  return (
    <Tooltip
      title={
        <Box>
          <Typography variant="body2">{entry.subject.name}</Typography>
          <Typography variant="caption">
            <Person sx={{ fontSize: 14, verticalAlign: 'middle' }} /> {entry.teacher.firstName} {entry.teacher.lastName}
          </Typography>
          <br />
          <Typography variant="caption">
            <Room sx={{ fontSize: 14, verticalAlign: 'middle' }} /> {entry.room.name}
          </Typography>
        </Box>
      }
    >
      <Box
        sx={{
          backgroundColor,
          color: 'white',
          borderRadius: 1,
          p: 1,
          mb: 0.5,
          cursor: 'grab',
          opacity: isDragging ? 0.5 : 1,
          boxShadow: isDragging ? 3 : 1,
          transition: 'all 0.2s',
          '&:hover': {
            boxShadow: 2,
            transform: 'scale(1.02)'
          }
        }}
      >
        <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block' }}>
          {entry.subject.code}
        </Typography>
        <Typography variant="caption" sx={{ display: 'block', opacity: 0.9 }}>
          {entry.classGroup.code}
        </Typography>
        <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
          <Chip
            size="small"
            label={entry.teacher.code}
            icon={<Person />}
            sx={{ 
              height: 16, 
              fontSize: '0.65rem',
              backgroundColor: 'rgba(255,255,255,0.2)',
              color: 'white',
              '& .MuiChip-icon': { fontSize: 12 }
            }}
          />
          <Chip
            size="small"
            label={entry.room.code}
            icon={<Room />}
            sx={{ 
              height: 16, 
              fontSize: '0.65rem',
              backgroundColor: 'rgba(255,255,255,0.2)',
              color: 'white',
              '& .MuiChip-icon': { fontSize: 12 }
            }}
          />
        </Box>
      </Box>
    </Tooltip>
  );
};

export default ScheduleEntry; 