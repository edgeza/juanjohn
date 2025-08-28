/**
 * Assets Store - Zustand
 * 
 * Manages asset data, loading states, and related operations
 */

import { create } from 'zustand';
import { apiClient } from '@/lib/apiClient';

export interface Asset {
  symbol: string;
  name: string;
  category: string;
  price: number;
  change_24h: number;
  change_percent_24h: number;
  volume_24h: number;
  timestamp?: string;
}

interface AssetsState {
  // State
  assets: Asset[];
  isLoading: boolean;
  error: string | null;
  searchTerm: string;
  selectedCategory: string;
  currentPage: number;
  totalAssets: number;
  assetsPerPage: number;

  // Actions
  fetchAssets: (page?: number, limit?: number) => Promise<void>;
  setSearchTerm: (term: string) => void;
  setSelectedCategory: (category: string) => void;
  setCurrentPage: (page: number) => void;
  clearError: () => void;
}

// Lightweight assets store used by the assets listing page
export const useAssetsStore = create<AssetsState>((set, get) => ({
  // Initial state
  assets: [],
  isLoading: false,
  error: null,
  searchTerm: '',
  selectedCategory: 'all',
  currentPage: 1,
  totalAssets: 0,
  assetsPerPage: 50,

  // Actions
  fetchAssets: async (page = 1, limit = 50) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await apiClient.getAssets(page, limit);
      
      // Debug logging
      console.log('API Response:', response);
      
      // The API client returns the response directly
      const data = response as any;
      console.log('Processed data:', data);
      console.log('Assets count:', data.assets?.length || 0);
      console.log('Total:', data.total || 0);
      
      set({ 
        assets: data.assets || [], 
        totalAssets: data.total || 0, 
        isLoading: false,
        currentPage: page
      });
    } catch (error: any) {
      console.error('Error fetching assets:', error);
      set({ 
        error: error.message || 'Failed to fetch assets', 
        isLoading: false 
      });
    }
  },

  setSearchTerm: (term: string) => set({ searchTerm: term }),
  setSelectedCategory: (category: string) => set({ selectedCategory: category }),
  setCurrentPage: (page: number) => set({ currentPage: page }),
  clearError: () => set({ error: null }),
}));
