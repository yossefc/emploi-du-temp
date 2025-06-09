import { useCallback, useEffect, useRef, useState } from 'react';

// Types pour l'accessibilité
export interface AccessibilityPreferences {
  reducedMotion: boolean;
  highContrast: boolean;
  largeText: boolean;
  screenReader: boolean;
  keyboardNavigation: boolean;
  darkMode: boolean;
  forceFocus: boolean;
}

export interface FocusOptions {
  preventScroll?: boolean;
  restoreOnUnmount?: boolean;
  selectText?: boolean;
}

export interface AnnouncementOptions {
  priority?: 'polite' | 'assertive';
  delay?: number;
  clear?: boolean;
}

// Hook pour gérer les préférences d'accessibilité
export function useAccessibilityPreferences(): [AccessibilityPreferences, (prefs: Partial<AccessibilityPreferences>) => void] {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>(() => {
    // Détecter les préférences système
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches;
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Charger les préférences sauvegardées
    const saved = localStorage.getItem('accessibility-preferences');
    const savedPrefs = saved ? JSON.parse(saved) : {};

    return {
      reducedMotion: prefersReducedMotion,
      highContrast: prefersHighContrast,
      largeText: false,
      screenReader: detectScreenReader(),
      keyboardNavigation: false,
      darkMode: prefersDarkMode,
      forceFocus: false,
      ...savedPrefs,
    };
  });

  const updatePreferences = useCallback((newPrefs: Partial<AccessibilityPreferences>) => {
    setPreferences(prev => {
      const updated = { ...prev, ...newPrefs };
      localStorage.setItem('accessibility-preferences', JSON.stringify(updated));
      
      // Appliquer les préférences au DOM
      applyPreferencesToDOM(updated);
      
      return updated;
    });
  }, []);

  useEffect(() => {
    applyPreferencesToDOM(preferences);
    
    // Écouter les changements de préférences système
    const mediaQueries = [
      { query: '(prefers-reduced-motion: reduce)', pref: 'reducedMotion' },
      { query: '(prefers-contrast: high)', pref: 'highContrast' },
      { query: '(prefers-color-scheme: dark)', pref: 'darkMode' },
    ];

    const listeners: Array<{ mq: MediaQueryList; listener: () => void }> = [];

    mediaQueries.forEach(({ query, pref }) => {
      const mq = window.matchMedia(query);
      const listener = () => {
        updatePreferences({ [pref]: mq.matches } as Partial<AccessibilityPreferences>);
      };
      
      mq.addEventListener('change', listener);
      listeners.push({ mq, listener });
    });

    return () => {
      listeners.forEach(({ mq, listener }) => {
        mq.removeEventListener('change', listener);
      });
    };
  }, [preferences, updatePreferences]);

  return [preferences, updatePreferences];
}

// Hook pour gérer le focus de manière accessible
export function useFocusManagement() {
  const previouslyFocusedElement = useRef<HTMLElement | null>(null);
  const focusStack = useRef<HTMLElement[]>([]);

  const focus = useCallback((element: HTMLElement | null, options: FocusOptions = {}) => {
    if (!element) return;

    const { preventScroll = false, restoreOnUnmount = true, selectText = false } = options;

    // Sauvegarder l'élément précédent si nécessaire
    if (restoreOnUnmount && document.activeElement instanceof HTMLElement) {
      previouslyFocusedElement.current = document.activeElement;
    }

    // Ajouter à la pile de focus
    focusStack.current.push(element);

    // Appliquer le focus
    element.focus({ preventScroll });

    // Sélectionner le texte si demandé
    if (selectText && element instanceof HTMLInputElement) {
      element.select();
    }
  }, []);

  const restoreFocus = useCallback(() => {
    if (previouslyFocusedElement.current) {
      previouslyFocusedElement.current.focus();
      previouslyFocusedElement.current = null;
    }
  }, []);

  const trapFocus = useCallback((container: HTMLElement) => {
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ) as NodeListOf<HTMLElement>;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;

      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);

    // Focus le premier élément
    if (firstElement) {
      firstElement.focus();
    }

    return () => {
      container.removeEventListener('keydown', handleTabKey);
    };
  }, []);

  const createFocusRing = useCallback((element: HTMLElement) => {
    // Ajouter un focus ring visible programmatiquement
    element.style.outline = '2px solid #4f46e5';
    element.style.outlineOffset = '2px';

    return () => {
      element.style.outline = '';
      element.style.outlineOffset = '';
    };
  }, []);

  return {
    focus,
    restoreFocus,
    trapFocus,
    createFocusRing,
    focusStack: focusStack.current,
  };
}

// Hook pour les annonces aux lecteurs d'écran
export function useScreenReaderAnnouncement() {
  const [announcer, setAnnouncer] = useState<HTMLElement | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // Créer l'élément d'annonce
    const announcerElement = document.createElement('div');
    announcerElement.setAttribute('aria-live', 'polite');
    announcerElement.setAttribute('aria-atomic', 'true');
    announcerElement.style.position = 'absolute';
    announcerElement.style.left = '-10000px';
    announcerElement.style.width = '1px';
    announcerElement.style.height = '1px';
    announcerElement.style.overflow = 'hidden';
    
    document.body.appendChild(announcerElement);
    setAnnouncer(announcerElement);

    return () => {
      if (announcerElement.parentNode) {
        announcerElement.parentNode.removeChild(announcerElement);
      }
    };
  }, []);

  const announce = useCallback((message: string, options: AnnouncementOptions = {}) => {
    if (!announcer) return;

    const { priority = 'polite', delay = 0, clear = true } = options;

    // Changer la priorité si nécessaire
    if (announcer.getAttribute('aria-live') !== priority) {
      announcer.setAttribute('aria-live', priority);
    }

    const makeAnnouncement = () => {
      if (clear) {
        announcer.textContent = '';
        // Force reflow pour que le screen reader détecte le changement
        announcer.offsetHeight;
      }
      announcer.textContent = message;
    };

    if (delay > 0) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(makeAnnouncement, delay);
    } else {
      makeAnnouncement();
    }
  }, [announcer]);

  const clearAnnouncement = useCallback(() => {
    if (announcer) {
      announcer.textContent = '';
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }, [announcer]);

  return {
    announce,
    clearAnnouncement,
  };
}

// Hook pour la navigation au clavier
export function useKeyboardNavigation() {
  const [keyboardUser, setKeyboardUser] = useState(false);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab') {
        setKeyboardUser(true);
      }
    };

    const handleMouseDown = () => {
      setKeyboardUser(false);
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleMouseDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleMouseDown);
    };
  }, []);

  const handleKeyPress = useCallback((
    event: React.KeyboardEvent,
    callback: () => void,
    keys: string[] = ['Enter', ' ']
  ) => {
    if (keys.includes(event.key)) {
      event.preventDefault();
      callback();
    }
  }, []);

  const createKeyboardHandler = useCallback((
    callback: () => void,
    keys: string[] = ['Enter', ' ']
  ) => ({
    onKeyDown: (event: React.KeyboardEvent) => handleKeyPress(event, callback, keys),
    tabIndex: 0,
    role: 'button',
  }), [handleKeyPress]);

  return {
    keyboardUser,
    handleKeyPress,
    createKeyboardHandler,
  };
}

// Hook pour les skip links
export function useSkipLinks() {
  const skipLinksRef = useRef<HTMLElement[]>([]);

  const addSkipLink = useCallback((target: string, label: string) => {
    const skipLink = document.createElement('a');
    skipLink.href = `#${target}`;
    skipLink.textContent = label;
    skipLink.className = 'sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 focus:bg-indigo-600 focus:text-white focus:p-2 focus:z-50';
    
    // Insérer au début du body
    document.body.insertBefore(skipLink, document.body.firstChild);
    skipLinksRef.current.push(skipLink);

    return () => {
      if (skipLink.parentNode) {
        skipLink.parentNode.removeChild(skipLink);
      }
      skipLinksRef.current = skipLinksRef.current.filter(link => link !== skipLink);
    };
  }, []);

  const removeAllSkipLinks = useCallback(() => {
    skipLinksRef.current.forEach(link => {
      if (link.parentNode) {
        link.parentNode.removeChild(link);
      }
    });
    skipLinksRef.current = [];
  }, []);

  useEffect(() => {
    return removeAllSkipLinks;
  }, [removeAllSkipLinks]);

  return {
    addSkipLink,
    removeAllSkipLinks,
  };
}

// Hook pour les landmarks ARIA
export function useLandmarks() {
  const landmarksRef = useRef<Map<string, HTMLElement>>(new Map());

  const registerLandmark = useCallback((id: string, element: HTMLElement, role: string, label?: string) => {
    element.setAttribute('role', role);
    element.id = id;
    
    if (label) {
      element.setAttribute('aria-label', label);
    }

    landmarksRef.current.set(id, element);

    return () => {
      landmarksRef.current.delete(id);
    };
  }, []);

  const navigateToLandmark = useCallback((id: string) => {
    const element = landmarksRef.current.get(id);
    if (element) {
      element.focus();
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  const getLandmarks = useCallback(() => {
    return Array.from(landmarksRef.current.entries()).map(([id, element]) => ({
      id,
      element,
      role: element.getAttribute('role'),
      label: element.getAttribute('aria-label'),
    }));
  }, []);

  return {
    registerLandmark,
    navigateToLandmark,
    getLandmarks,
  };
}

// Hook pour la gestion des modal accessibles
export function useAccessibleModal() {
  const { trapFocus, restoreFocus } = useFocusManagement();
  const { announce } = useScreenReaderAnnouncement();
  const previousBodyOverflow = useRef<string>('');

  const openModal = useCallback((modalElement: HTMLElement, title: string) => {
    // Sauvegarder et bloquer le scroll
    previousBodyOverflow.current = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    // Annoncer l'ouverture du modal
    announce(`Modal ouvert: ${title}`);

    // Piéger le focus
    const releaseFocusTrap = trapFocus(modalElement);

    // Gérer la fermeture avec Escape
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        closeModal();
      }
    };

    document.addEventListener('keydown', handleEscape);

    const closeModal = () => {
      // Restaurer le scroll
      document.body.style.overflow = previousBodyOverflow.current;
      
      // Restaurer le focus
      restoreFocus();
      
      // Annoncer la fermeture
      announce('Modal fermé');
      
      // Nettoyer les événements
      document.removeEventListener('keydown', handleEscape);
      releaseFocusTrap();
    };

    return closeModal;
  }, [trapFocus, restoreFocus, announce]);

  return { openModal };
}

// Hook pour les formulaires accessibles
export function useAccessibleForm() {
  const { announce } = useScreenReaderAnnouncement();

  const announceErrors = useCallback((errors: Record<string, string>) => {
    const errorCount = Object.keys(errors).length;
    if (errorCount > 0) {
      const message = `${errorCount} erreur${errorCount > 1 ? 's' : ''} de validation détectée${errorCount > 1 ? 's' : ''}`;
      announce(message, { priority: 'assertive' });
    }
  }, [announce]);

  const announceSuccess = useCallback((message: string) => {
    announce(message, { priority: 'polite' });
  }, [announce]);

  const createFieldProps = useCallback((
    fieldName: string,
    error?: string,
    description?: string
  ) => {
    const props: any = {
      id: fieldName,
      'aria-invalid': !!error,
    };

    if (error) {
      props['aria-describedby'] = `${fieldName}-error`;
    } else if (description) {
      props['aria-describedby'] = `${fieldName}-description`;
    }

    return props;
  }, []);

  return {
    announceErrors,
    announceSuccess,
    createFieldProps,
  };
}

// Utilitaires d'accessibilité
function detectScreenReader(): boolean {
  // Détecter les lecteurs d'écran courants
  const userAgent = navigator.userAgent.toLowerCase();
  return (
    userAgent.includes('nvda') ||
    userAgent.includes('jaws') ||
    userAgent.includes('voiceover') ||
    userAgent.includes('talkback') ||
    !!window.speechSynthesis
  );
}

function applyPreferencesToDOM(preferences: AccessibilityPreferences): void {
  const root = document.documentElement;

  // Appliquer les classes CSS basées sur les préférences
  root.classList.toggle('reduce-motion', preferences.reducedMotion);
  root.classList.toggle('high-contrast', preferences.highContrast);
  root.classList.toggle('large-text', preferences.largeText);
  root.classList.toggle('dark-mode', preferences.darkMode);
  root.classList.toggle('force-focus', preferences.forceFocus);

  // Définir les variables CSS personnalisées
  root.style.setProperty('--animation-duration', preferences.reducedMotion ? '0.01ms' : '');
  root.style.setProperty('--font-size-scale', preferences.largeText ? '1.2' : '1');
}

// Composant d'accessibilité global
export function useGlobalAccessibility() {
  const [preferences, updatePreferences] = useAccessibilityPreferences();
  const { keyboardUser } = useKeyboardNavigation();
  const { addSkipLink } = useSkipLinks();

  useEffect(() => {
    // Ajouter les skip links par défaut
    const removeMainSkip = addSkipLink('main-content', 'Aller au contenu principal');
    const removeNavSkip = addSkipLink('main-navigation', 'Aller à la navigation');

    return () => {
      removeMainSkip();
      removeNavSkip();
    };
  }, [addSkipLink]);

  // Ajouter une classe au body pour indiquer l'utilisation du clavier
  useEffect(() => {
    document.body.classList.toggle('keyboard-user', keyboardUser);
  }, [keyboardUser]);

  return {
    preferences,
    updatePreferences,
    keyboardUser,
  };
}

export default useAccessibilityPreferences;