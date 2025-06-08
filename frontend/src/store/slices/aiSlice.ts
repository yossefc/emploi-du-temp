import { createSlice, createAsyncThunk, PayloadAction, ActionReducerMapBuilder } from '@reduxjs/toolkit';
import api from '../../services/api';

interface AIMessage {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  suggestions?: string[];
}

interface Suggestion {
  id: number;
  type: 'constraint' | 'optimization' | 'conflict';
  description: string;
  priority: 'high' | 'medium' | 'low';
  action?: any;
}

interface AIState {
  messages: AIMessage[];
  suggestions: Suggestion[];
  isProcessing: boolean;
  error: string | null;
  currentContext: any;
}

const initialState: AIState = {
  messages: [],
  suggestions: [],
  isProcessing: false,
  error: null,
  currentContext: null,
};

// Async thunks
export const sendMessage = createAsyncThunk(
  'ai/sendMessage',
  async ({ message, context }: { message: string; context?: any }) => {
    const response = await api.sendAIMessage(message, context);
    return response.data;
  }
);

export const parseConstraints = createAsyncThunk(
  'ai/parseConstraints',
  async (text: string) => {
    const response = await api.parseConstraints(text);
    return response.data;
  }
);

export const fetchSuggestions = createAsyncThunk(
  'ai/fetchSuggestions',
  async (scheduleId: number) => {
    const response = await api.getSuggestions(scheduleId);
    return response.data;
  }
);

export const explainConflict = createAsyncThunk(
  'ai/explainConflict',
  async (conflictId: number) => {
    const response = await api.explainConflict(conflictId);
    return response.data;
  }
);

const aiSlice = createSlice({
  name: 'ai',
  initialState,
  reducers: {
    addMessage: (state: AIState, action: PayloadAction<AIMessage>) => {
      state.messages.push(action.payload);
    },
    clearMessages: (state: AIState) => {
      state.messages = [];
    },
    setContext: (state: AIState, action: PayloadAction<any>) => {
      state.currentContext = action.payload;
    },
    clearError: (state: AIState) => {
      state.error = null;
    },
    removeSuggestion: (state: AIState, action: PayloadAction<number>) => {
      state.suggestions = state.suggestions.filter((s: Suggestion) => s.id !== action.payload);
    },
  },
  extraReducers: (builder: ActionReducerMapBuilder<AIState>) => {
    // Send message
    builder
      .addCase(sendMessage.pending, (state: AIState) => {
        state.isProcessing = true;
        state.error = null;
      })
      .addCase(sendMessage.fulfilled, (state: AIState, action: PayloadAction<any>) => {
        state.isProcessing = false;
        
        // Ajouter le message de l'IA
        const aiMessage: AIMessage = {
          id: Date.now().toString(),
          text: action.payload.message,
          sender: 'ai',
          timestamp: new Date(),
          suggestions: action.payload.suggestions,
        };
        state.messages.push(aiMessage);
        
        // Mettre à jour le contexte si fourni
        if (action.payload.context) {
          state.currentContext = action.payload.context;
        }
      })
      .addCase(sendMessage.rejected, (state: AIState, action: any) => {
        state.isProcessing = false;
        state.error = action.error.message || 'Failed to send message';
      });

    // Parse constraints
    builder
      .addCase(parseConstraints.pending, (state: AIState) => {
        state.isProcessing = true;
        state.error = null;
      })
      .addCase(parseConstraints.fulfilled, (state: AIState, action: PayloadAction<any>) => {
        state.isProcessing = false;
        
        // Ajouter un message de confirmation
        const confirmMessage: AIMessage = {
          id: Date.now().toString(),
          text: `J'ai identifié ${action.payload.constraints.length} contraintes dans votre texte.`,
          sender: 'ai',
          timestamp: new Date(),
        };
        state.messages.push(confirmMessage);
      })
      .addCase(parseConstraints.rejected, (state: AIState, action: any) => {
        state.isProcessing = false;
        state.error = action.error.message || 'Failed to parse constraints';
      });

    // Fetch suggestions
    builder
      .addCase(fetchSuggestions.pending, (state: AIState) => {
        state.isProcessing = true;
        state.error = null;
      })
      .addCase(fetchSuggestions.fulfilled, (state: AIState, action: PayloadAction<Suggestion[]>) => {
        state.isProcessing = false;
        state.suggestions = action.payload;
      })
      .addCase(fetchSuggestions.rejected, (state: AIState, action: any) => {
        state.isProcessing = false;
        state.error = action.error.message || 'Failed to fetch suggestions';
      });

    // Explain conflict
    builder
      .addCase(explainConflict.fulfilled, (state: AIState, action: PayloadAction<any>) => {
        // Ajouter l'explication comme message
        const explanationMessage: AIMessage = {
          id: Date.now().toString(),
          text: action.payload.explanation,
          sender: 'ai',
          timestamp: new Date(),
          suggestions: action.payload.suggestions,
        };
        state.messages.push(explanationMessage);
      });
  },
});

export const {
  addMessage,
  clearMessages,
  setContext,
  clearError,
  removeSuggestion,
} = aiSlice.actions;

export default aiSlice.reducer; 