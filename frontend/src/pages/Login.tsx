import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Link,
  FormControlLabel,
  Checkbox,
  Container
} from '@mui/material';
import { Login as LoginIcon } from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { login, clearError } from '../store/slices/authSlice';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { isLoading, error } = useAppSelector(state => state.auth);
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'rememberMe' ? checked : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Clear any previous errors
    dispatch(clearError());
    
    try {
      // Use the Redux thunk action
      const result = await dispatch(login({
        email: formData.email,
        password: formData.password
      }));
      
      if (login.fulfilled.match(result)) {
        navigate('/dashboard');
      }
    } catch (error) {
      // Error is handled by the rejected case in the slice
      console.error('Login error:', error);
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ padding: 4, width: '100%' }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Box
              sx={{
                backgroundColor: 'primary.main',
                color: 'white',
                borderRadius: '50%',
                width: 56,
                height: 56,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 2
              }}
            >
              <LoginIcon />
            </Box>
            
            <Typography component="h1" variant="h5">
              Connexion
            </Typography>
            
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Générateur d'Emplois du Temps
            </Typography>
          </Box>

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            <TextField
              required
              fullWidth
              id="email"
              label="Adresse email"
              name="email"
              autoComplete="email"
              autoFocus
              value={formData.email}
              onChange={handleChange}
              sx={{ mb: 2 }}
            />
            
            <TextField
              required
              fullWidth
              name="password"
              label="Mot de passe"
              type="password"
              id="password"
              autoComplete="current-password"
              value={formData.password}
              onChange={handleChange}
              sx={{ mb: 2 }}
            />
            
            <FormControlLabel
              control={
                <Checkbox
                  name="rememberMe"
                  color="primary"
                  checked={formData.rememberMe}
                  onChange={handleChange}
                />
              }
              label="Se souvenir de moi"
            />
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={isLoading}
            >
              {isLoading ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                'Se connecter'
              )}
            </Button>
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Link
                component="button"
                variant="body2"
                onClick={(e) => {
                  e.preventDefault();
                  navigate('/forgot-password');
                }}
              >
                Mot de passe oublié ?
              </Link>
              
              <Link
                component="button"
                variant="body2"
                onClick={(e) => {
                  e.preventDefault();
                  navigate('/register');
                }}
              >
                Créer un compte
              </Link>
            </Box>
            
            {/* Crédentiels de test pour le développement */}
            {process.env.NODE_ENV === 'development' && (
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="caption">
                  <strong>Test:</strong> admin@example.com / password123
                </Typography>
              </Alert>
            )}
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default LoginPage; 