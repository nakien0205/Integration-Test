'use client';

import { motion } from 'framer-motion';
import { useState, useRef, useEffect } from 'react';
import ProductCard from './ProductCard';
import SearchBar from './SearchBar';
import Sidebar from './Sidebar';
import ProfilePopup from './ProfilePopup';
import PersonalizationPopup from './PersonalizationPopup';
import SettingsPopup from './SettingsPopup';
import EmailUpdatePopup from './EmailUpdatePopup';
import PasswordUpdatePopup from './PasswordUpdatePopup';
import HelpPopup from './HelpPopup';

interface ResultsPageProps {
  onSearch: (query: string) => void;
  username?: string;
  email?: string;
  onLogout?: () => void;
  onHomeClick?: () => void;
  onSettingsClick?: () => void;
  onPersonalizationClick?: () => void;
  onHelpClick?: () => void;
  onEmailUpdate?: (email: string) => void;
  onLogoClick?: () => void;
  chatHistory?: Array<{ role: 'user' | 'ai'; content: string; timestamp?: string; error?: boolean; details?: string }>;
  searchQuery?: string;
  chatSessions?: Array<{
    id: string;
    timestamp: string;
    messages: Array<{ role: 'user' | 'ai'; content: string; timestamp?: string }>;
    preview: string;
  }>;
  onRestoreSession?: (sessionId: string) => void;
  onDeleteSession?: (sessionId: string) => void;
}

export default function ResultsPage({
  onSearch,
  username = 'ENUID',
  email = 'user@example.com',
  onLogout,
  onHomeClick,
  onSettingsClick,
  onPersonalizationClick,
  onHelpClick,
  onEmailUpdate,
  onLogoClick,
  chatHistory = [],
  searchQuery,
  chatSessions = [],
  onRestoreSession,
  onDeleteSession,
}: ResultsPageProps) {
  const [showProfilePopup, setShowProfilePopup] = useState(false);
  const [showPersonalization, setShowPersonalization] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showEmailUpdate, setShowEmailUpdate] = useState(false);
  const [showPasswordUpdate, setShowPasswordUpdate] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col md:flex-row transition-colors duration-300">
      {/* Sidebar - Desktop Only */}
      <div className="hidden md:block">
        <Sidebar
          onHomeClick={onHomeClick}
          onProfileClick={() => setShowProfilePopup(true)}
          onSettingsClick={() => setShowSettings(true)}
          onLogoClick={onLogoClick}
          activeTab="home"
          showProfilePopup={showProfilePopup}
          chatSessions={chatSessions}
          onRestoreSession={onRestoreSession}
          onDeleteSession={onDeleteSession}
        />
      </div>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 z-40 transition-colors duration-300">
        <div className="flex items-center justify-around py-3 px-4">
          <button
            onClick={onHomeClick}
            className="flex flex-col items-center gap-1 text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white transition-colors"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            <span className="text-xs">Home</span>
          </button>
          <button
            onClick={() => setShowSettings(true)}
            className="flex flex-col items-center gap-1 text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white transition-colors"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="text-xs">Settings</span>
          </button>
          <button
            onClick={() => setShowProfilePopup(true)}
            className="flex flex-col items-center gap-1 text-gray-500 hover:text-black dark:text-gray-400 dark:hover:text-white transition-colors"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <span className="text-xs">Profile</span>
          </button>
        </div>
      </nav>

      {/* Profile Popup */}
      <ProfilePopup
        isOpen={showProfilePopup}
        onClose={() => setShowProfilePopup(false)}
        username={username}
        email={email}
        onPersonalizationClick={() => {
          setShowProfilePopup(false);
          setShowPersonalization(true);
        }}
        onSettingsClick={() => {
          setShowProfilePopup(false);
          setShowSettings(true);
        }}
        onHelpClick={() => setShowHelp(true)}
        onLogout={onLogout}
      />

      {/* Personalization Popup */}
      <PersonalizationPopup
        isOpen={showPersonalization}
        onClose={() => setShowPersonalization(false)}
        username={username}
        email={email}
        onSave={(data) => {
          console.log('Personalization saved:', data);
          setShowPersonalization(false);
        }}
      />

      {/* Settings Popup */}
      <SettingsPopup
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        onEmailChange={() => {
          setShowSettings(false);
          setShowEmailUpdate(true);
        }}
        onPasswordChange={() => {
          setShowSettings(false);
          setShowPasswordUpdate(true);
        }}
      />

      {/* Email Update Popup */}
      <EmailUpdatePopup
        isOpen={showEmailUpdate}
        onClose={() => setShowEmailUpdate(false)}
        currentEmail={email}
        onSendOTP={async (newEmail) => {
          try {
            const response = await fetch('/api/otp/send', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email: newEmail, username: username }),
            });
            const data = await response.json();
            return data.success;
          } catch (error) {
            console.error('Send OTP error:', error);
            return false;
          }
        }}
        onVerify={async (newEmail, otp, password) => {
          try {
            const { Client, Account } = await import('appwrite');
            const client = new Client()
              .setEndpoint(process.env.NEXT_PUBLIC_APPWRITE_ENDPOINT || 'https://cloud.appwrite.io/v1')
              .setProject(process.env.NEXT_PUBLIC_APPWRITE_PROJECT_ID || '');
            const account = new Account(client);
            
            await account.updateEmail(newEmail, password);
            console.log('✅ Email updated in Appwrite');
            
            onEmailUpdate?.(newEmail);
            localStorage.setItem('user_email', newEmail);
            
            return true;
          } catch (error: any) {
            console.error('❌ Appwrite email update error:', error);
            return false;
          }
        }}
      />

      {/* Password Update Popup */}
      <PasswordUpdatePopup
        isOpen={showPasswordUpdate}
        onClose={() => setShowPasswordUpdate(false)}
        onUpdate={async (oldPassword, newPassword) => {
          try {
            const { Client, Account } = await import('appwrite');
            const client = new Client()
              .setEndpoint(process.env.NEXT_PUBLIC_APPWRITE_ENDPOINT || 'https://cloud.appwrite.io/v1')
              .setProject(process.env.NEXT_PUBLIC_APPWRITE_PROJECT_ID || '');
            const account = new Account(client);
            
            await account.updatePassword(newPassword, oldPassword);
            return true;
          } catch (error: any) {
            console.error('Password update error:', error);
            return false;
          }
        }}
        onForgotPassword={async () => {
          try {
            const { Client, Account } = await import('appwrite');
            const client = new Client()
              .setEndpoint(process.env.NEXT_PUBLIC_APPWRITE_ENDPOINT || 'https://cloud.appwrite.io/v1')
              .setProject(process.env.NEXT_PUBLIC_APPWRITE_PROJECT_ID || '');
            const account = new Account(client);

            const user = await account.get();
            const customName = localStorage.getItem('user_custom_name') || user.name || '';

            const recoveryUrl = `${window.location.origin}/auth/reset-password`;
            await account.createRecovery(user.email, recoveryUrl);
            
            alert('Password reset email sent! Please check your inbox.');
            
            try {
              await fetch('/api/password-reset/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                  email: user.email,
                  username: customName
                }),
              });
            } catch (err) {
              console.log('Custom email failed, but Appwrite email sent');
            }
          } catch (error: any) {
            console.error('❌ Forgot password error:', error);
            alert('Failed to send password reset email. Please try again.');
          }
        }}
      />

      {/* Help Popup */}
      <HelpPopup isOpen={showHelp} onClose={() => setShowHelp(false)} />

      {/* Floating Search Bar - Bottom Center */}
      <motion.div
        initial={{ opacity: 0, y: 50, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ 
          type: 'spring',
          stiffness: 260,
          damping: 20,
          delay: 0.1
        }}
        className="fixed bottom-24 md:bottom-8 left-1/2 md:left-[calc(50%+2.5rem)] -translate-x-1/2 z-30 w-full max-w-2xl px-4 md:px-0"
      >
        <motion.div
          whileHover={{ scale: 1.02, y: -2 }}
          transition={{ type: 'spring', stiffness: 400, damping: 25 }}
          className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border-2 border-gray-200 dark:border-gray-700 overflow-hidden backdrop-blur-lg bg-opacity-95 dark:bg-opacity-95 focus-within:border-black dark:focus-within:border-white transition-colors duration-200"
        >
          <div className="relative">
            <textarea
              placeholder="Continue chatting..."
              rows={2}
              style={{ minHeight: '3.5rem' }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  const target = e.target as HTMLTextAreaElement
                  if (target.value.trim()) {
                    onSearch(target.value);
                    target.value = '';
                  }
                }
              }}
              className="w-full px-6 py-4 text-base bg-transparent border-none focus:outline-none text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 resize-none max-h-32 overflow-y-auto"
            />
            <motion.button
              whileHover={{ scale: 1.1, rotate: 90 }}
              whileTap={{ scale: 0.9 }}
              onClick={(e) => {
                const input = e.currentTarget.previousElementSibling as HTMLTextAreaElement;
                if (input && input.value.trim()) {
                  onSearch(input.value);
                  input.value = '';
                }
              }}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-xl hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </motion.button>
          </div>
        </motion.div>
      </motion.div>

      {/* Main Content */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="flex-1 md:ml-16 pb-32 md:pb-24 pt-8"
      >
        {/* Chat History Section */}
        <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8">
          <motion.h2
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-xl sm:text-2xl font-bold text-black dark:text-white mb-2"
          >
            CHAT
          </motion.h2>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-sm sm:text-base text-gray-600 dark:text-gray-400 mb-6 sm:mb-8"
          >
            Your conversation with AI
          </motion.p>

          {/* Chat Messages */}
          <div className="space-y-4 mb-8">
            {chatHistory.map((message, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl p-4 shadow-md ${
                    message.role === 'user'
                      ? 'bg-black dark:bg-white text-white dark:text-black'
                      : message.error
                      ? 'bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-700'
                      : 'bg-white dark:bg-gray-800 text-black dark:text-white'
                  }`}
                >
                  {message.role === 'ai' && message.error ? (
                    <div>
                      <h3 className="text-lg font-semibold mb-2 text-red-700 dark:text-red-400">
                        ⚠️ Connection Error
                      </h3>
                      <p className="text-red-700 dark:text-red-400 font-medium mb-2">{message.content}</p>
                      {message.details && (
                        <details className="mt-4">
                          <summary className="text-sm text-red-600 dark:text-red-400 cursor-pointer hover:text-red-800 dark:hover:text-red-300">
                            Technical Details
                          </summary>
                          <pre className="text-xs text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30 p-3 rounded mt-2 overflow-auto">
                            {message.details}
                          </pre>
                        </details>
                      )}
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  )}
                  {message.timestamp && (
                    <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-gray-300 dark:text-gray-600' : 'text-gray-500 dark:text-gray-400'}`}>
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </p>
                  )}
                </div>
              </motion.div>
            ))}
            <div ref={chatEndRef} />
          </div>
        </div>
      </motion.div>
    </div>
  );
}
