import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

interface OptimizationTask {
  id: string;
  symbol: string;
  strategy: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILURE';
  progress: number;
  createdAt: string;
}

interface OptimizationState {
  tasks: OptimizationTask[];
  isLoading: boolean;
  error: string | null;
}

const initialState: OptimizationState = {
  tasks: [],
  isLoading: false,
  error: null,
};

const optimizationSlice = createSlice({
  name: 'optimization',
  initialState,
  reducers: {
    addTask: (state, action: PayloadAction<OptimizationTask>) => {
      state.tasks.unshift(action.payload);
    },
    updateTask: (state, action: PayloadAction<{ id: string; updates: Partial<OptimizationTask> }>) => {
      const index = state.tasks.findIndex(task => task.id === action.payload.id);
      if (index !== -1) {
        state.tasks[index] = { ...state.tasks[index], ...action.payload.updates } as OptimizationTask;
      }
    },
    removeTask: (state, action: PayloadAction<string>) => {
      state.tasks = state.tasks.filter(task => task.id !== action.payload);
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const { addTask, updateTask, removeTask, setLoading, setError } = optimizationSlice.actions;
export default optimizationSlice.reducer;
