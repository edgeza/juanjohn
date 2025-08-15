import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

interface Symbol {
  symbol: string;
  name: string;
  exchange: string;
}

interface DataState {
  symbols: Symbol[];
  selectedSymbol: string | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: DataState = {
  symbols: [],
  selectedSymbol: null,
  isLoading: false,
  error: null,
};

const dataSlice = createSlice({
  name: 'data',
  initialState,
  reducers: {
    setSymbols: (state, action: PayloadAction<Symbol[]>) => {
      state.symbols = action.payload;
    },
    setSelectedSymbol: (state, action: PayloadAction<string>) => {
      state.selectedSymbol = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
  },
});

export const { setSymbols, setSelectedSymbol, setLoading, setError } = dataSlice.actions;
export default dataSlice.reducer;
