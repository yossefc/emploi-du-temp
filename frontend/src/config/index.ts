/**
 * Configuration globale de l'application
 */

// Récupération des variables d'environnement
const getEnvVar = (key: string, defaultValue: string = ''): string => {
  if (typeof window !== 'undefined' && (window as any).__ENV__) {
    return (window as any).__ENV__[key] || defaultValue;
  }
  return defaultValue;
};

export const config = {
  // API Configuration
  api: {
    baseUrl: getEnvVar('VITE_API_BASE_URL', 'http://localhost:8000'),
    timeout: 30000,
  },
  
  // Environment
  environment: 'development',
  isDevelopment: true,
  isProduction: false,
  
  // Feature flags
  features: {
    // Désactiver MSW en développement pour utiliser le vrai backend
    useMockApi: getEnvVar('VITE_USE_MOCK_API', 'false') === 'true',
    enableDevtools: true,
    enableAnalytics: false,
  },
  
  // App settings
  app: {
    name: 'School Timetable Manager',
    version: '1.0.0',
    defaultLanguage: 'fr',
    supportedLanguages: ['fr', 'he'],
  },
  
  // Auth settings
  auth: {
    tokenKey: 'access_token',
    refreshTokenKey: 'refresh_token',
    tokenExpiration: 24 * 60 * 60 * 1000, // 24 hours
  },
  
  // UI settings
  ui: {
    itemsPerPage: 10,
    maxItemsPerPage: 100,
    defaultTheme: 'light',
  },
};

// Helper functions
export const isFeatureEnabled = (feature: keyof typeof config.features): boolean => {
  return config.features[feature];
};

export const getApiUrl = (endpoint: string): string => {
  const baseUrl = config.api.baseUrl.replace(/\/$/, ''); // Remove trailing slash
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
};

export default config; 