'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/apiClient';
import type { UserResponse } from '@/types/user';
import { useAuthStore } from '@/store/authStore';

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    username: '',
    email: '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  useEffect(() => {
    // Check if user is authenticated
    if (!isAuthenticated || !user) {
      router.replace('/login');
      return;
    }

    // Set form data from user
    setEditForm(prev => ({
      ...prev,
      username: user.username,
      email: user.email
    }));
    setLoading(false);
  }, [user, isAuthenticated, router]);

  const handleLogout = async () => {
    try {
      await apiClient.logout();
      logout();
      router.replace('/login');
    } catch (e: any) {
      console.error('Logout failed:', e);
      // Even if API fails, clear local state and redirect
      logout();
      router.replace('/login');
    }
  };

  const handleEditProfile = async () => {
    try {
      if (editForm.newPassword && editForm.newPassword !== editForm.confirmPassword) {
        setError('New passwords do not match');
        return;
      }

      // Here you would typically call an API endpoint to update the profile
      // For now, we'll just show a success message
      setError(null);
      setIsEditing(false);
      // TODO: Implement profile update API call
    } catch (e: any) {
      setError(e.message || 'Failed to update profile');
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditForm(prev => ({
      ...prev,
      username: user?.username || '',
      email: user?.email || '',
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    }));
    setError(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading profile...</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Profile</h1>
        <p className="text-gray-400">Manage your account settings and preferences</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile Information */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass p-6 rounded-lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Profile Information</h2>
              {!isEditing && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="btn-secondary px-4 py-2"
                >
                  Edit Profile
                </button>
              )}
            </div>

            {!isEditing ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Username</label>
                  <div className="text-lg">{user.username}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Email</label>
                  <div className="text-lg">{user.email}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Account Status</label>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      user.has_access 
                        ? 'bg-green-500/20 text-green-400' 
                        : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {user.has_access ? 'Active' : 'Pending Approval'}
                    </span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Role</label>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      user.is_admin 
                        ? 'bg-purple-500/20 text-purple-400' 
                        : 'bg-blue-500/20 text-blue-400'
                    }`}>
                      {user.is_admin ? 'Administrator' : 'User'}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Username</label>
                  <input
                    type="text"
                    value={editForm.username}
                    onChange={(e) => setEditForm(prev => ({ ...prev, username: e.target.value }))}
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Email</label>
                  <input
                    type="email"
                    value={editForm.email}
                    onChange={(e) => setEditForm(prev => ({ ...prev, email: e.target.value }))}
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Current Password</label>
                  <input
                    type="password"
                    value={editForm.currentPassword}
                    onChange={(e) => setEditForm(prev => ({ ...prev, currentPassword: e.target.value }))}
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-blue-500"
                    placeholder="Enter current password to confirm changes"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">New Password</label>
                  <input
                    type="password"
                    value={editForm.newPassword}
                    onChange={(e) => setEditForm(prev => ({ ...prev, newPassword: e.target.value }))}
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-blue-500"
                    placeholder="Leave blank to keep current password"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Confirm New Password</label>
                  <input
                    type="password"
                    value={editForm.confirmPassword}
                    onChange={(e) => setEditForm(prev => ({ ...prev, confirmPassword: e.target.value }))}
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-blue-500"
                    placeholder="Confirm new password"
                  />
                </div>
                <div className="flex gap-3 pt-2">
                  <button
                    onClick={handleEditProfile}
                    className="btn-primary px-4 py-2"
                  >
                    Save Changes
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    className="btn-secondary px-4 py-2"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Subscription Information */}
          <div className="glass p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Subscription</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Current Plan</label>
                <div className="text-lg">Free Tier</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Status</label>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400">
                    Active
                  </span>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Next Billing</label>
                <div className="text-lg">N/A</div>
              </div>
              <button className="btn-primary px-4 py-2">
                Upgrade Plan
              </button>
            </div>
          </div>

          {/* Account Actions */}
          <div className="glass p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Account Actions</h2>
            <div className="space-y-3">
              <button
                onClick={handleLogout}
                className="w-full btn-secondary px-4 py-2 text-left"
              >
                Logout
              </button>
              <button className="w-full btn-secondary px-4 py-2 text-left text-red-400 hover:text-red-300">
                Delete Account
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="glass p-6 rounded-lg">
            <h3 className="text-lg font-semibold mb-4">Quick Stats</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-400">Member Since</span>
                <span>{new Date(user.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Last Login</span>
                <span>Today</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">API Calls</span>
                <span>0/1000</span>
              </div>
            </div>
          </div>

          {/* Admin Quick Actions */}
          {user.is_admin && (
            <div className="glass p-6 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Admin Actions</h3>
              <div className="space-y-3">
                <button
                  onClick={() => router.push('/admin')}
                  className="w-full btn-primary px-4 py-2 text-left"
                >
                  Manage Users
                </button>
                <button className="w-full btn-secondary px-4 py-2 text-left">
                  System Settings
                </button>
                <button className="w-full btn-secondary px-4 py-2 text-left">
                  View Logs
                </button>
              </div>
            </div>
          )}

          {/* Help & Support */}
          <div className="glass p-6 rounded-lg">
            <h3 className="text-lg font-semibold mb-4">Help & Support</h3>
            <div className="space-y-3">
              <button className="w-full btn-secondary px-4 py-2 text-left">
                Documentation
              </button>
              <button className="w-full btn-secondary px-4 py-2 text-left">
                Contact Support
              </button>
              <button className="w-full btn-secondary px-4 py-2 text-left">
                Report Bug
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
