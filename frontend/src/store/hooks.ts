import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';
import type { RootState, AppDispatch } from './store';

// Hooks typés pour Redux
// Utilisez ces hooks au lieu de useDispatch et useSelector dans vos composants

// Hook dispatch typé
export const useAppDispatch: () => AppDispatch = useDispatch;

// Hook selector typé
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

// Type helper pour les actions thunk (optionnel)
export type { AppDispatch, RootState } from './store'; 