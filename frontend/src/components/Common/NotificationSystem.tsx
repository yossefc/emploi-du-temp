import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon,
  ArrowPathIcon,
  EyeIcon,
  ClockIcon,
  BellIcon
} from '@heroicons/react/24/outline';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent';

export interface NotificationAction {
  label: string;
  onClick: () => void;
  type?: 'primary' | 'secondary' | 'danger';
}

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  priority?: NotificationPriority;
  persistent?: boolean;
  autoHide?: boolean;
  duration?: number;
  actions?: NotificationAction[];
  onDismiss?: () => void;
  onRetry?: () => void;
  retryCount?: number;
  maxRetries?: number;
  timestamp: Date;
  read?: boolean;
  data?: any; // Additional data for the notification
}

interface NotificationContextType {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => string;
  removeNotification: (id: string) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearAll: () => void;
  retryNotification: (id: string) => void;
  getUnreadCount: () => number;
  showHistory: boolean;
  toggleHistory: () => void;
}

const NotificationContext = createContext<NotificationContextType | null>(null);

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: React.ReactNode;
  maxNotifications?: number;
  defaultDuration?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
}

export function NotificationProvider({
  children,
  maxNotifications = 5,
  defaultDuration = 5000,
  position = 'top-right'
}: NotificationProviderProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newNotification: Notification = {
      id,
      timestamp: new Date(),
      duration: defaultDuration,
      autoHide: true,
      priority: 'normal',
      retryCount: 0,
      maxRetries: 3,
      read: false,
      ...notification
    };

    setNotifications(prev => {
      // Sort by priority and timestamp
      const priorityOrder = { urgent: 4, high: 3, normal: 2, low: 1 };
      const updatedNotifications = [newNotification, ...prev]
        .sort((a, b) => {
          const priorityDiff = priorityOrder[b.priority!] - priorityOrder[a.priority!];
          if (priorityDiff !== 0) return priorityDiff;
          return b.timestamp.getTime() - a.timestamp.getTime();
        })
        .slice(0, maxNotifications);

      return updatedNotifications;
    });

    // Auto-hide notification
    if (newNotification.autoHide && !newNotification.persistent) {
      setTimeout(() => {
        removeNotification(id);
      }, newNotification.duration);
    }

    return id;
  }, [defaultDuration, maxNotifications]);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const markAsRead = useCallback((id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  const retryNotification = useCallback((id: string) => {
    const notification = notifications.find(n => n.id === id);
    if (notification?.onRetry && notification.retryCount! < notification.maxRetries!) {
      setNotifications(prev => 
        prev.map(n => 
          n.id === id 
            ? { ...n, retryCount: (n.retryCount || 0) + 1 }
            : n
        )
      );
      notification.onRetry();
    }
  }, [notifications]);

  const getUnreadCount = useCallback(() => {
    return notifications.filter(n => !n.read).length;
  }, [notifications]);

  const toggleHistory = useCallback(() => {
    setShowHistory(prev => !prev);
  }, []);

  return (
    <NotificationContext.Provider value={{
      notifications,
      addNotification,
      removeNotification,
      markAsRead,
      markAllAsRead,
      clearAll,
      retryNotification,
      getUnreadCount,
      showHistory,
      toggleHistory
    }}>
      {children}
      <NotificationContainer position={position} />
      {showHistory && <NotificationHistory />}
    </NotificationContext.Provider>
  );
}

interface NotificationContainerProps {
  position: string;
}

function NotificationContainer({ position }: NotificationContainerProps) {
  const { notifications } = useNotifications();

  const getPositionClasses = () => {
    const baseClasses = 'fixed z-50 p-4 space-y-4 pointer-events-none';
    switch (position) {
      case 'top-right':
        return `${baseClasses} top-0 right-0`;
      case 'top-left':
        return `${baseClasses} top-0 left-0`;
      case 'bottom-right':
        return `${baseClasses} bottom-0 right-0`;
      case 'bottom-left':
        return `${baseClasses} bottom-0 left-0`;
      case 'top-center':
        return `${baseClasses} top-0 left-1/2 transform -translate-x-1/2`;
      case 'bottom-center':
        return `${baseClasses} bottom-0 left-1/2 transform -translate-x-1/2`;
      default:
        return `${baseClasses} top-0 right-0`;
    }
  };

  return (
    <div className={getPositionClasses()}>
      {notifications
        .filter(n => !n.persistent)
        .slice(0, 5)
        .map(notification => (
          <NotificationItem key={notification.id} notification={notification} />
        ))}
    </div>
  );
}

interface NotificationItemProps {
  notification: Notification;
}

function NotificationItem({ notification }: NotificationItemProps) {
  const { removeNotification, markAsRead, retryNotification } = useNotifications();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
    return () => setIsVisible(false);
  }, []);

  const handleDismiss = useCallback(() => {
    setIsVisible(false);
    setTimeout(() => {
      removeNotification(notification.id);
      notification.onDismiss?.();
    }, 300);
  }, [notification, removeNotification]);

  const handleRetry = useCallback(() => {
    retryNotification(notification.id);
  }, [notification.id, retryNotification]);

  const handleMarkAsRead = useCallback(() => {
    markAsRead(notification.id);
  }, [notification.id, markAsRead]);

  const getTypeIcon = () => {
    const iconClasses = "h-5 w-5";
    switch (notification.type) {
      case 'success':
        return <CheckCircleIcon className={`${iconClasses} text-green-500`} />;
      case 'error':
        return <ExclamationCircleIcon className={`${iconClasses} text-red-500`} />;
      case 'warning':
        return <ExclamationTriangleIcon className={`${iconClasses} text-yellow-500`} />;
      case 'info':
        return <InformationCircleIcon className={`${iconClasses} text-blue-500`} />;
    }
  };

  const getTypeStyles = () => {
    switch (notification.type) {
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'info':
        return 'bg-blue-50 border-blue-200';
    }
  };

  const getPriorityBorder = () => {
    switch (notification.priority) {
      case 'urgent':
        return 'border-l-4 border-l-red-600';
      case 'high':
        return 'border-l-4 border-l-orange-500';
      case 'normal':
        return 'border-l-4 border-l-blue-500';
      case 'low':
        return 'border-l-4 border-l-gray-400';
      default:
        return '';
    }
  };

  return (
    <div
      className={`
        max-w-sm w-full shadow-lg rounded-lg border pointer-events-auto
        transform transition-all duration-300 ease-in-out
        ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
        ${getTypeStyles()} ${getPriorityBorder()}
        ${!notification.read ? 'ring-2 ring-indigo-500 ring-opacity-50' : ''}
      `}
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            {getTypeIcon()}
          </div>
          
          <div className="ml-3 w-0 flex-1">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-gray-900">
                {notification.title}
              </p>
              
              {notification.priority === 'urgent' && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                  Urgent
                </span>
              )}
            </div>
            
            {notification.message && (
              <p className="mt-1 text-sm text-gray-600">
                {notification.message}
              </p>
            )}
            
            {/* Retry info */}
            {notification.onRetry && notification.retryCount! > 0 && (
              <p className="mt-1 text-xs text-gray-500">
                Tentative {notification.retryCount}/{notification.maxRetries}
              </p>
            )}
            
            {/* Actions */}
            {(notification.actions || notification.onRetry) && (
              <div className="mt-3 flex space-x-2">
                {notification.actions?.map((action, index) => (
                  <button
                    key={index}
                    onClick={action.onClick}
                    className={`
                      inline-flex items-center px-3 py-1.5 border text-xs font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2
                      ${action.type === 'danger'
                        ? 'border-red-300 text-red-700 bg-red-50 hover:bg-red-100 focus:ring-red-500'
                        : action.type === 'primary'
                        ? 'border-transparent text-white bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500'
                        : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50 focus:ring-indigo-500'
                      }
                    `}
                  >
                    {action.label}
                  </button>
                ))}
                
                {notification.onRetry && notification.retryCount! < notification.maxRetries! && (
                  <button
                    onClick={handleRetry}
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    <ArrowPathIcon className="w-3 h-3 mr-1" />
                    Réessayer
                  </button>
                )}
              </div>
            )}
          </div>
          
          <div className="ml-4 flex flex-col space-y-1">
            {!notification.read && (
              <button
                onClick={handleMarkAsRead}
                className="text-gray-400 hover:text-gray-600 focus:outline-none"
                title="Marquer comme lu"
              >
                <EyeIcon className="h-4 w-4" />
              </button>
            )}
            
            <button
              onClick={handleDismiss}
              className="text-gray-400 hover:text-gray-600 focus:outline-none"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function NotificationHistory() {
  const { notifications, showHistory, toggleHistory, clearAll, markAllAsRead } = useNotifications();
  const [filter, setFilter] = useState<NotificationType | 'all'>('all');

  const filteredNotifications = notifications.filter(n => 
    filter === 'all' || n.type === filter
  );

  if (!showHistory) return null;

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity z-50">
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          <div className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <BellIcon className="h-6 w-6 text-gray-400" />
                <h3 className="text-lg font-medium text-gray-900">
                  Historique des notifications
                </h3>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                  {notifications.length}
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={markAllAsRead}
                  className="text-sm text-indigo-600 hover:text-indigo-900"
                >
                  Tout marquer comme lu
                </button>
                <button
                  onClick={clearAll}
                  className="text-sm text-red-600 hover:text-red-900"
                >
                  Tout effacer
                </button>
                <button
                  onClick={toggleHistory}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
            </div>

            {/* Filters */}
            <div className="px-6 py-3 border-b border-gray-200">
              <div className="flex space-x-2">
                {['all', 'success', 'error', 'warning', 'info'].map(type => (
                  <button
                    key={type}
                    onClick={() => setFilter(type as any)}
                    className={`
                      px-3 py-1 rounded-full text-xs font-medium
                      ${filter === type
                        ? 'bg-indigo-100 text-indigo-800'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }
                    `}
                  >
                    {type === 'all' ? 'Toutes' : type}
                  </button>
                ))}
              </div>
            </div>

            {/* Notifications List */}
            <div className="max-h-96 overflow-y-auto">
              {filteredNotifications.length === 0 ? (
                <div className="px-6 py-12 text-center text-gray-500">
                  <BellIcon className="mx-auto h-12 w-12 text-gray-300" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">Aucune notification</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Aucune notification ne correspond à vos filtres.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {filteredNotifications.map(notification => (
                    <div
                      key={notification.id}
                      className={`
                        px-6 py-4 hover:bg-gray-50
                        ${!notification.read ? 'bg-blue-50' : ''}
                      `}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0">
                          {notification.type === 'success' && <CheckCircleIcon className="h-5 w-5 text-green-500" />}
                          {notification.type === 'error' && <ExclamationCircleIcon className="h-5 w-5 text-red-500" />}
                          {notification.type === 'warning' && <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />}
                          {notification.type === 'info' && <InformationCircleIcon className="h-5 w-5 text-blue-500" />}
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-gray-900">
                              {notification.title}
                            </p>
                            <div className="flex items-center space-x-2">
                              {!notification.read && (
                                <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                              )}
                              <p className="text-xs text-gray-500 flex items-center">
                                <ClockIcon className="w-3 h-3 mr-1" />
                                {notification.timestamp.toLocaleTimeString()}
                              </p>
                            </div>
                          </div>
                          
                          {notification.message && (
                            <p className="mt-1 text-sm text-gray-600">
                              {notification.message}
                            </p>
                          )}
                          
                          <div className="mt-1 flex items-center space-x-2">
                            <span className={`
                              inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
                              ${notification.priority === 'urgent' ? 'bg-red-100 text-red-800' :
                                notification.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                                notification.priority === 'normal' ? 'bg-blue-100 text-blue-800' :
                                'bg-gray-100 text-gray-800'}
                            `}>
                              {notification.priority}
                            </span>
                            
                            <span className={`
                              inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
                              ${notification.type === 'success' ? 'bg-green-100 text-green-800' :
                                notification.type === 'error' ? 'bg-red-100 text-red-800' :
                                notification.type === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-blue-100 text-blue-800'}
                            `}>
                              {notification.type}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Utility functions for easy notification creation
export const notify = {
  success: (title: string, options?: Partial<Notification>) => {
    const { addNotification } = useNotifications();
    return addNotification({ type: 'success', title, ...options });
  },
  error: (title: string, options?: Partial<Notification>) => {
    const { addNotification } = useNotifications();
    return addNotification({ type: 'error', title, persistent: true, ...options });
  },
  warning: (title: string, options?: Partial<Notification>) => {
    const { addNotification } = useNotifications();
    return addNotification({ type: 'warning', title, ...options });
  },
  info: (title: string, options?: Partial<Notification>) => {
    const { addNotification } = useNotifications();
    return addNotification({ type: 'info', title, ...options });
  }
};

export default NotificationProvider;