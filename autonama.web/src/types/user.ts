// User types for Autonama Trading System

export interface UserResponse {
  id: string;
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
  isActive: boolean;
  is_admin: boolean;
  has_access: boolean;
  created_at: string;
  updated_at?: string;
  lastLoginAt?: string;
  preferences?: UserPreferences;
  subscription?: SubscriptionInfo;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  timezone: string;
  currency: string;
  language: string;
  notifications: NotificationSettings;
  trading: TradingPreferences;
}

export interface NotificationSettings {
  email: boolean;
  push: boolean;
  sms: boolean;
  signals: boolean;
  alerts: boolean;
  optimization: boolean;
  marketUpdates: boolean;
}

export interface TradingPreferences {
  defaultTimeframe: string;
  riskTolerance: 'low' | 'medium' | 'high';
  preferredAssets: string[];
  autoTrading: boolean;
  stopLossPercentage: number;
  takeProfitPercentage: number;
}

export interface SubscriptionInfo {
  plan: 'free' | 'basic' | 'pro' | 'enterprise';
  status: 'active' | 'canceled' | 'expired' | 'trial';
  startDate: string;
  endDate?: string;
  features: string[];
  limits: SubscriptionLimits;
}

export interface SubscriptionLimits {
  maxAssets: number;
  maxStrategies: number;
  maxOptimizations: number;
  maxAlerts: number;
  dataRetentionDays: number;
  apiCallsPerHour: number;
}

export interface LoginRequest {
  username: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  firstName?: string;
  lastName?: string;
  acceptTerms: boolean;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  newPassword: string;
  confirmPassword: string;
}

export interface UserUpdateRequest {
  firstName?: string;
  lastName?: string;
  email?: string;
  preferences?: Partial<UserPreferences>;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

// Auth response types
export interface AuthResponse {
  user: UserResponse;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface TokenRefreshRequest {
  refreshToken: string;
}

export interface TokenRefreshResponse {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

// Session types
export interface Session {
  user: UserResponse;
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
  isAuthenticated: boolean;
}

// Permission types
export interface Permission {
  id: string;
  name: string;
  description: string;
  resource: string;
  action: string;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Permission[];
}


