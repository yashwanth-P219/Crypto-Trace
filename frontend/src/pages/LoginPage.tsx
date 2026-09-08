import React, { useState } from 'react';
import { Shield, User, Lock, ArrowRight, ShieldAlert } from 'lucide-react';
import { api } from '../services/api';
import { User as UserType } from '../types';

interface LoginPageProps {
  onLoginSuccess: (user: UserType) => void;
  onSwitchToSignup?: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess, onSwitchToSignup }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await api.login(username, password);
      onLoginSuccess(data.user);
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 p-0.5 shadow-md mx-auto flex items-center justify-center">
          <div className="w-full h-full bg-[#0F172A] rounded-[14px] flex items-center justify-center">
            <Shield className="w-7 h-7 text-blue-400" />
          </div>
        </div>
        <h2 className="mt-4 text-2xl font-black tracking-tight text-[#1E293B]">
          CryptoTrace FORENSICS
        </h2>
        <p className="mt-1 text-xs text-slate-500 font-medium">
          Cryptocurrency Fraud & VASP Identification Platform
        </p>
        <span className="inline-block mt-2 text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700">
          CYBERCRIME DEFENSE PORTAL
        </span>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="bg-white border border-slate-200 py-8 px-6 shadow-sm rounded-2xl sm:px-10 space-y-6">
          {error && (
            <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 shrink-0 text-red-600" />
              <span className="font-medium">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Username / Officer ID
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="block w-full pl-9 pr-3 py-2.5 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
                  placeholder="e.g. investigator"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-9 pr-3 py-2.5 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-bold text-white bg-[#2563EB] hover:bg-blue-700 shadow-sm transition-all disabled:opacity-50"
            >
              {loading ? (
                <span>Authenticating Officer...</span>
              ) : (
                <>
                  <span>Sign In to Terminal</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>

            {/* Quick Demo Access Credentials */}
            <div className="pt-2 border-t border-slate-100">
              <p className="text-[11px] font-semibold text-slate-500 mb-2 text-center">
                Quick Demo Accounts (1-Click Fill):
              </p>
              <div className="grid grid-cols-3 gap-2 text-[10px]">
                <button
                  type="button"
                  onClick={() => {
                    setUsername('investigator');
                    setPassword('password123');
                  }}
                  className="py-1.5 px-2 rounded-lg bg-blue-50 border border-blue-200 text-blue-700 font-bold hover:bg-blue-100 transition-colors text-center"
                >
                  Investigator
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setUsername('supervisor');
                    setPassword('password123');
                  }}
                  className="py-1.5 px-2 rounded-lg bg-purple-50 border border-purple-200 text-purple-700 font-bold hover:bg-purple-100 transition-colors text-center"
                >
                  Supervisor
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setUsername('admin');
                    setPassword('password123');
                  }}
                  className="py-1.5 px-2 rounded-lg bg-slate-100 border border-slate-200 text-slate-700 font-bold hover:bg-slate-200 transition-colors text-center"
                >
                  Admin
                </button>
              </div>
            </div>

            {onSwitchToSignup && (
              <div className="border-t border-slate-100 pt-3 text-center">
                <p className="text-xs text-slate-500">
                  New to CryptoTrace?{' '}
                  <button
                    type="button"
                    onClick={onSwitchToSignup}
                    className="font-bold text-blue-600 hover:text-blue-700 transition-colors ml-1"
                  >
                    Register as Victim or Investigator
                  </button>
                </p>
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};
