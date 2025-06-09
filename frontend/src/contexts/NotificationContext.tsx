import React, { createContext, useContext, ReactNode } from 'react';

interface NotificationContextType {
  // Add notification context methods here if needed
  notify: (message: string) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const notify = (message: string) => {
    // Simple console log for now - replace with actual notification system
    console.log('Notification:', message);
  };

  const value = {
    notify,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
}; 