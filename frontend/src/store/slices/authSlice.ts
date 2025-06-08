import { 
  createSlice, 
  createAsyncThunk, 
  PayloadAction, 
  ActionReducerMapBuilder
} from '@reduxjs/toolkit';
import api from '../../services/api';

interface User {
  id: string;
  email: string;
  username: string;
  role: 'admin' | 'teacher' | 'viewer';
  languagePreference: 'fr' | 'he';
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
};

// Async thunks
export const login = createAsyncThunk<
  User, // return type
  { email: string; password: string }, // arg type
  { rejectValue: string }
>(
  'auth/login',
  async ({ email, password }, { rejectWithValue }) => {
    try {
      const response = await api.login(email, password);
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      return response.data.user;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Login failed');
    }
  }
);

export const logout = createAsyncThunk<
  void, // return type
  void, // no arg
  { rejectValue: string }
>(
  'auth/logout', 
  async (_, { rejectWithValue }) => {
    try {
      await api.logout();
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Logout failed');
    }
  }
);

export const register = createAsyncThunk<
  User, // return type
  { username: string; email: string; password: string; role?: string }, // arg type
  { rejectValue: string }
>(
  'auth/register',
  async (userData, { rejectWithValue }) => {
    try {
      const response = await api.register(userData);
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      return response.data.user;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.message || 'Registration failed');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setUser: (state: AuthState, action: PayloadAction<User>) => {
      state.user = action.payload;
      state.isAuthenticated = true;
    },
    clearError: (state: AuthState) => {
      state.error = null;
    },
    updateLanguagePreference: (state: AuthState, action: PayloadAction<'fr' | 'he'>) => {
      if (state.user) {
        state.user.languagePreference = action.payload;
      }
    },
  },
  extraReducers: (builder: ActionReducerMapBuilder<AuthState>) => {
    // Login
    builder
      .addCase(login.pending, (state: AuthState) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state: AuthState, action: PayloadAction<User>) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.user = action.payload;
      })
      .addCase(login.rejected, (state: AuthState, action) => {
        state.isLoading = false;
        state.error = action.payload as string || action.error?.message || 'Login failed';
      });

    // Logout
    builder
      .addCase(logout.fulfilled, (state: AuthState) => {
        state.user = null;
        state.isAuthenticated = false;
      })
      .addCase(logout.rejected, (state: AuthState, action) => {
        state.error = action.payload as string || 'Logout failed';
      });

    // Register
    builder
      .addCase(register.pending, (state: AuthState) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state: AuthState, action: PayloadAction<User>) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.user = action.payload;
      })
      .addCase(register.rejected, (state: AuthState, action) => {
        state.isLoading = false;
        state.error = action.payload as string || action.error?.message || 'Registration failed';
      });
  },
});

export const { setUser, clearError, updateLanguagePreference } = authSlice.actions;
export default authSlice.reducer; 