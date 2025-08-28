'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/apiClient';
import type { UserResponse } from '@/types/user';
import { useRouter } from 'next/navigation';

type AdminUser = { 
  id: number; 
  username: string; 
  email: string; 
  has_access: boolean; 
  is_admin: boolean; 
  created_at: string 
};

export default function AdminPage() {
  const router = useRouter();
  const [me, setMe] = useState<UserResponse | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const current = await apiClient.getCurrentUser();
        if (!current.is_admin) {
          router.replace('/');
          return;
        }
        setMe(current);
        const list = await apiClient.adminListUsers();
        setUsers(list);
      } catch (e: any) {
        if (e.status === 401) {
          router.replace('/login');
          return;
        }
        setError(e.message || 'Failed to load users');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [router]);

  const grant = async (username: string) => {
    try {
      setActionLoading(username);
      await apiClient.adminGrant(username);
      setUsers(prev => prev.map(u => u.username === username ? { ...u, has_access: true } : u));
    } catch (e: any) {
      setError(e.message || 'Failed to grant access');
    } finally {
      setActionLoading(null);
    }
  };

  const revoke = async (username: string) => {
    try {
      setActionLoading(username);
      await apiClient.adminRevoke(username);
      setUsers(prev => prev.map(u => u.username === username ? { ...u, has_access: false } : u));
    } catch (e: any) {
      setError(e.message || 'Failed to revoke access');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading admin panel...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen p-6">
        <div className="max-w-4xl mx-auto">
          <div className="p-6 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
            {error}
          </div>
        </div>
      </div>
    );
  }

  if (!me) {
    return null;
  }

  const pendingUsers = users.filter(u => !u.has_access);
  const activeUsers = users.filter(u => u.has_access);

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Admin Panel</h1>
          <p className="text-gray-400">Manage user access and system settings</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="glass p-6 rounded-lg">
            <div className="text-2xl font-bold text-blue-400">{users.length}</div>
            <div className="text-sm text-gray-400">Total Users</div>
          </div>
          <div className="glass p-6 rounded-lg">
            <div className="text-2xl font-bold text-green-400">{activeUsers.length}</div>
            <div className="text-sm text-gray-400">Active Users</div>
          </div>
          <div className="glass p-6 rounded-lg">
            <div className="text-2xl font-bold text-yellow-400">{pendingUsers.length}</div>
            <div className="text-sm text-gray-400">Pending Approval</div>
          </div>
          <div className="glass p-6 rounded-lg">
            <div className="text-2xl font-bold text-purple-400">{users.filter(u => u.is_admin).length}</div>
            <div className="text-sm text-gray-400">Administrators</div>
          </div>
        </div>

        {/* Pending Users Section */}
        {pendingUsers.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4 text-yellow-400">
              ⚠️ Pending User Approvals ({pendingUsers.length})
            </h2>
            <div className="glass p-6 rounded-lg border border-yellow-500/20">
              <div className="overflow-auto rounded-lg">
                <table className="min-w-full text-sm">
                  <thead className="bg-yellow-500/10">
                    <tr>
                      <th className="text-left p-3 text-yellow-400">Username</th>
                      <th className="text-left p-3 text-yellow-400">Email</th>
                      <th className="text-left p-3 text-yellow-400">Registered</th>
                      <th className="text-left p-3 text-yellow-400">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingUsers.map(u => (
                      <tr key={u.id} className="border-t border-yellow-500/10">
                        <td className="p-3 font-medium">{u.username}</td>
                        <td className="p-3 opacity-80">{u.email}</td>
                        <td className="p-3 opacity-80">
                          {new Date(u.created_at).toLocaleDateString()}
                        </td>
                        <td className="p-3">
                          <button
                            onClick={() => grant(u.username)}
                            disabled={actionLoading === u.username}
                            className="px-4 py-2 rounded bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {actionLoading === u.username ? 'Processing...' : 'Approve Access'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* All Users Section */}
        <div>
          <h2 className="text-xl font-semibold mb-4">All Users</h2>
          <div className="glass p-6 rounded-lg">
            <div className="overflow-auto rounded-lg">
              <table className="min-w-full text-sm">
                <thead className="bg-white/5">
                  <tr>
                    <th className="text-left p-3">Username</th>
                    <th className="text-left p-3">Email</th>
                    <th className="text-left p-3">Role</th>
                    <th className="text-left p-3">Status</th>
                    <th className="text-left p-3">Registered</th>
                    <th className="text-left p-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id} className="border-t border-white/10">
                      <td className="p-3 font-medium">{u.username}</td>
                      <td className="p-3 opacity-80">{u.email}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          u.is_admin 
                            ? 'bg-purple-500/20 text-purple-400' 
                            : 'bg-blue-500/20 text-blue-400'
                        }`}>
                          {u.is_admin ? 'Admin' : 'User'}
                        </span>
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          u.has_access 
                            ? 'bg-green-500/20 text-green-400' 
                            : 'bg-yellow-500/20 text-yellow-400'
                        }`}>
                          {u.has_access ? 'Active' : 'Pending'}
                        </span>
                      </td>
                      <td className="p-3 opacity-80">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td className="p-3 flex gap-2">
                        {u.has_access ? (
                          <button
                            onClick={() => revoke(u.username)}
                            disabled={actionLoading === u.username}
                            className="px-3 py-1 rounded bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {actionLoading === u.username ? '...' : 'Revoke'}
                          </button>
                        ) : (
                          <button
                            onClick={() => grant(u.username)}
                            disabled={actionLoading === u.username}
                            className="px-3 py-1 rounded bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {actionLoading === u.username ? '...' : 'Grant'}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="flex gap-4">
            <button className="btn-primary px-6 py-3">
              Export User List
            </button>
            <button className="btn-secondary px-6 py-3">
              System Settings
            </button>
            <button className="btn-secondary px-6 py-3">
              View System Logs
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}


