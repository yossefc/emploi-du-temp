import React, { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Alert,
  Fab,
  Tooltip
} from '@mui/material';
import {
  Add,
  Download,
  PlayArrow,
  Chat
} from '@mui/icons-material';
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
      <Box sx={{ flexGrow: 1, position: 'relative' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4">
            Emploi du temps
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            {currentSchedule && (
              <>
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={() => handleExport('excel')}
                >
                  Excel
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={() => handleExport('pdf')}
                >
                  PDF
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={() => handleExport('ics')}
                >
                  Calendrier
                </Button>
              </>
            )}
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setOpenGenerate(true)}
            >
              Générer
            </Button>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {isLoading ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <CircularProgress size={60} />
            <Typography variant="h6" sx={{ mt: 2 }}>
              Génération en cours...
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              Cela peut prendre quelques minutes selon la complexité
            </Typography>
          </Paper>
        ) : currentSchedule ? (
          <Grid container spacing={3}>
            <Grid item xs={12} lg={showChat ? 8 : 12}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="h6">
                    {currentSchedule.name}
                  </Typography>
                  {currentSchedule.conflicts && currentSchedule.conflicts.length > 0 && (
                    <Alert severity="warning" sx={{ py: 0 }}>
                      {currentSchedule.conflicts.length} conflit(s) détecté(s)
                    </Alert>
                  )}
                </Box>
                <ScheduleGrid
                  schedule={currentSchedule}
                  onUpdate={handleScheduleUpdate}
                  readOnly={false}
                />
              </Paper>
            </Grid>
            
            {showChat && (
              <Grid item xs={12} lg={4}>
                <Paper sx={{ height: '80vh', display: 'flex', flexDirection: 'column' }}>
                  <ChatInterface
                    onSendMessage={handleAIMessage}
                    language="fr"
                  />
                </Paper>
              </Grid>
            )}
          </Grid>
        ) : (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              Aucun emploi du temps sélectionné
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Cliquez sur "Générer" pour créer un nouvel emploi du temps
            </Typography>
          </Paper>
        )}

        {/* FAB pour ouvrir/fermer le chat */}
        {currentSchedule && (
          <Tooltip title={showChat ? "Fermer l'assistant" : "Ouvrir l'assistant IA"}>
            <Fab
              color="primary"
              sx={{
                position: 'fixed',
                bottom: 24,
                right: 24
              }}
              onClick={() => setShowChat(!showChat)}
            >
              <Chat />
            </Fab>
          </Tooltip>
        )}

        {/* Dialog de génération */}
        <Dialog open={openGenerate} onClose={() => setOpenGenerate(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Générer un nouvel emploi du temps</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Nom de l'emploi du temps"
              fullWidth
              variant="outlined"
              value={scheduleName}
              onChange={(e) => setScheduleName(e.target.value)}
              placeholder="Ex: Emploi du temps 2024 - Semestre 1"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenGenerate(false)}>
              Annuler
            </Button>
            <Button
              onClick={handleGenerateSchedule}
              variant="contained"
              disabled={!scheduleName.trim() || isLoading}
              startIcon={isLoading ? <CircularProgress size={20} /> : <PlayArrow />}
            >
              {isLoading ? 'Génération...' : 'Générer'}
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Layout>
  );
};

export default SchedulePage; 