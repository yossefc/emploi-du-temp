import { createSlice, createAsyncThunk, PayloadAction, ActionReducerMapBuilder } from '@reduxjs/toolkit';
import api from '../../services/api';

interface Schedule {
  id: number;
  name: string;
  status: 'draft' | 'generated' | 'approved';
  solverStatus?: string;
  generationTime?: number;
  entries: any[];
  conflicts?: any[];
}

interface ScheduleState {
  schedules: Schedule[];
  currentSchedule: Schedule | null;
  isLoading: boolean;
  isGenerating: boolean;
  error: string | null;
  filters: {
    classId?: number;
    teacherId?: number;
    roomId?: number;
  };
}

const initialState: ScheduleState = {
  schedules: [],
  currentSchedule: null,
  isLoading: false,
  isGenerating: false,
  error: null,
  filters: {},
};

// Async thunks
export const fetchSchedules = createAsyncThunk(
  'schedule/fetchSchedules',
  async () => {
    const response = await api.getSchedules();
    return response.data;
  }
);

export const fetchSchedule = createAsyncThunk(
  'schedule/fetchSchedule',
  async (id: number) => {
    const response = await api.getSchedule(id);
    return response.data;
  }
);

export const generateSchedule = createAsyncThunk(
  'schedule/generate',
  async (params: any) => {
    const response = await api.generateSchedule(params);
    return response.data;
  }
);

export const updateScheduleEntry = createAsyncThunk(
  'schedule/updateEntry',
  async ({ scheduleId, entryData }: { scheduleId: number; entryData: any }) => {
    const response = await api.updateScheduleEntry(scheduleId, entryData);
    return response.data;
  }
);

export const exportSchedule = createAsyncThunk(
  'schedule/export',
  async ({ id, format }: { id: number; format: 'pdf' | 'excel' | 'ics' }) => {
    const response = await api.exportSchedule(id, format);
    
    // Créer un lien de téléchargement
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `schedule_${id}.${format}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    return { success: true };
  }
);

const scheduleSlice = createSlice({
  name: 'schedule',
  initialState,
  reducers: {
    setCurrentSchedule: (state: ScheduleState, action: PayloadAction<Schedule>) => {
      state.currentSchedule = action.payload;
    },
    updateFilters: (state: ScheduleState, action: PayloadAction<Partial<ScheduleState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state: ScheduleState) => {
      state.filters = {};
    },
    updateScheduleLocally: (state: ScheduleState, action: PayloadAction<any>) => {
      if (state.currentSchedule) {
        state.currentSchedule.entries = action.payload;
      }
    },
    clearError: (state: ScheduleState) => {
      state.error = null;
    },
  },
  extraReducers: (builder: ActionReducerMapBuilder<ScheduleState>) => {
    // Fetch schedules
    builder
      .addCase(fetchSchedules.pending, (state: ScheduleState) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchSchedules.fulfilled, (state: ScheduleState, action: PayloadAction<Schedule[]>) => {
        state.isLoading = false;
        state.schedules = action.payload;
      })
      .addCase(fetchSchedules.rejected, (state: ScheduleState, action: any) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch schedules';
      });

    // Fetch single schedule
    builder
      .addCase(fetchSchedule.pending, (state: ScheduleState) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchSchedule.fulfilled, (state: ScheduleState, action: PayloadAction<Schedule>) => {
        state.isLoading = false;
        state.currentSchedule = action.payload;
      })
      .addCase(fetchSchedule.rejected, (state: ScheduleState, action: any) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch schedule';
      });

    // Generate schedule
    builder
      .addCase(generateSchedule.pending, (state: ScheduleState) => {
        state.isGenerating = true;
        state.error = null;
      })
      .addCase(generateSchedule.fulfilled, (state: ScheduleState, action: PayloadAction<Schedule>) => {
        state.isGenerating = false;
        state.currentSchedule = action.payload;
        state.schedules.push(action.payload);
      })
      .addCase(generateSchedule.rejected, (state: ScheduleState, action: any) => {
        state.isGenerating = false;
        state.error = action.error.message || 'Failed to generate schedule';
      });

    // Update schedule entry
    builder
      .addCase(updateScheduleEntry.fulfilled, (state: ScheduleState, action: PayloadAction<Schedule>) => {
        if (state.currentSchedule) {
          state.currentSchedule = action.payload;
        }
      });
  },
});

export const {
  setCurrentSchedule,
  updateFilters,
  clearFilters,
  updateScheduleLocally,
  clearError,
} = scheduleSlice.actions;

export default scheduleSlice.reducer; 