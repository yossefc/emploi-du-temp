import React from 'react';
import {
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Box,
  LinearProgress,
  Chip
} from '@mui/material';
import {
  People,
  School,
  MeetingRoom,
  CalendarMonth,
  CheckCircle,
  Warning
} from '@mui/icons-material';
import { useAppSelector } from '../store/hooks';
import Layout from '../components/Common/Layout';

interface StatCard {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
}

const Dashboard: React.FC = () => {
  const { user } = useAppSelector(state => state.auth);
  const { currentSchedule } = useAppSelector(state => state.schedule);

  // Mock schedules data for stats
  const mockSchedules = currentSchedule ? [currentSchedule] : [];

  // Stats simulées - à remplacer par des vraies données
  const stats: StatCard[] = [
    {
      title: 'Enseignants',
      value: 45,
      icon: <People />,
      color: '#2196f3'
    },
    {
      title: 'Classes',
      value: 24,
      icon: <School />,
      color: '#4caf50'
    },
    {
      title: 'Salles',
      value: 30,
      icon: <MeetingRoom />,
      color: '#ff9800'
    },
    {
      title: 'Emplois du temps',
      value: mockSchedules.length,
      icon: <CalendarMonth />,
      color: '#9c27b0'
    }
  ];

  const recentSchedules = mockSchedules.slice(0, 5);

  return (
    <Layout>
      <Box sx={{ flexGrow: 1 }}>
        <Typography variant="h4" gutterBottom>
          Tableau de bord
        </Typography>
        
        <Typography variant="subtitle1" color="text.secondary" gutterBottom>
          Bienvenue, {user?.username} !
        </Typography>

        {/* Cartes de statistiques */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {stats.map((stat, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: 56,
                        height: 56,
                        borderRadius: '50%',
                        backgroundColor: `${stat.color}20`,
                        color: stat.color,
                        mr: 2
                      }}
                    >
                      {stat.icon}
                    </Box>
                    <Box>
                      <Typography color="text.secondary" variant="body2">
                        {stat.title}
                      </Typography>
                      <Typography variant="h4">
                        {stat.value}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Emplois du temps récents */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Emplois du temps récents
              </Typography>
              
              {recentSchedules.length === 0 ? (
                <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
                  Aucun emploi du temps généré
                </Typography>
              ) : (
                <Box>
                  {recentSchedules.map((schedule) => (
                    <Box
                      key={schedule.id}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        p: 2,
                        borderBottom: '1px solid',
                        borderColor: 'divider',
                        '&:last-child': { borderBottom: 0 }
                      }}
                    >
                      <Box>
                        <Typography variant="subtitle1">
                          {schedule.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Créé le {new Date().toLocaleDateString('fr-FR')}
                        </Typography>
                      </Box>
                      <Chip
                        label={schedule.status}
                        color={
                          schedule.status === 'approved' ? 'success' :
                          schedule.status === 'generated' ? 'primary' : 'default'
                        }
                        size="small"
                      />
                    </Box>
                  ))}
                </Box>
              )}
            </Paper>
          </Grid>

          {/* Statut du système */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Statut du système
              </Typography>
              
              <Box sx={{ mt: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CheckCircle color="success" sx={{ mr: 1 }} />
                  <Typography>Base de données : Connectée</Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CheckCircle color="success" sx={{ mr: 1 }} />
                  <Typography>Solver OR-Tools : Prêt</Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Warning color="warning" sx={{ mr: 1 }} />
                  <Typography>Agent IA : Configuration requise</Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <CheckCircle color="success" sx={{ mr: 1 }} />
                  <Typography>API : En ligne</Typography>
                </Box>
              </Box>
              
              <Box sx={{ mt: 3 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Utilisation mémoire
                </Typography>
                <LinearProgress variant="determinate" value={35} sx={{ mb: 1 }} />
                <Typography variant="caption" color="text.secondary">
                  35% (2.1 GB / 6 GB)
                </Typography>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Layout>
  );
};

export default Dashboard; 