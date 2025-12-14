'use client';

import { useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Client, Account, ID } from 'appwrite';
import GradientBackground from './components/GradientBackground';
import SignUpForm from './components/SignUpForm';
import SignInForm from './components/SignInForm';
import LoadingScreen from './components/LoadingScreen';
import SkeletonLoader from './components/SkeletonLoader';
import HomePage from './components/HomePage';
import ResultsPage from './components/ResultsPage';
import SettingsPage from './components/SettingsPage';
import PersonalizationPage from './components/PersonalizationPage';
import HelpPage from './components/HelpPage';

type AppState = 'auth' | 'loading' | 'skeleton' | 'home' | 'results' | 'settings' | 'personalization' | 'help';

// Initialize Appwrite client
const client = new Client()
  .setEndpoint(process.env.NEXT_PUBLIC_APPWRITE_ENDPOINT || 'https://cloud.appwrite.io/v1')
  .setProject(process.env.NEXT_PUBLIC_APPWRITE_PROJECT_ID || '');

const account = new Account(client);

export default function Home() {
  const [isSignUp, setIsSignUp] = useState(true);
  const [appState, setAppState] = useState<AppState>('auth');
  const [username, setUsername] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('user@example.com');
  const [error, setError] = useState<string>('');
  const [chatHistory, setChatHistory] = useState<Array<{ role: 'user' | 'ai'; content: string; timestamp?: string; error?: boolean; details?: string }>>([]);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [chatSessions, setChatSessions] = useState<Array<{
    id: string;
    timestamp: string;
    messages: Array<{ role: 'user' | 'ai'; content: string; timestamp?: string }>;
    preview: string;
  }>>([]);

  // Load chat sessions from localStorage on mount
  useEffect(() => {
    const savedSessions = localStorage.getItem('chat_sessions');
    if (savedSessions) {
      try {
        setChatSessions(JSON.parse(savedSessions));
      } catch (error) {
        console.error('Failed to load chat sessions:', error);
      }
    }
  }, []);

  // Save current chat session to localStorage
  const saveCurrentChatSession = () => {
    if (chatHistory.length === 0) return;

    const firstUserMessage = chatHistory.find(msg => msg.role === 'user');
    if (!firstUserMessage) return;

    const newSession = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      messages: chatHistory.filter(msg => !msg.error), // Don't save error messages
      preview: firstUserMessage.content.slice(0, 50) + (firstUserMessage.content.length > 50 ? '...' : ''),
    };

    const updatedSessions = [newSession, ...chatSessions].slice(0, 10); // Keep last 10 sessions
    setChatSessions(updatedSessions);
    localStorage.setItem('chat_sessions', JSON.stringify(updatedSessions));
  };

  // Restore a chat session
  const restoreChatSession = (sessionId: string) => {
    const session = chatSessions.find(s => s.id === sessionId);
    if (session) {
      setChatHistory(session.messages);
      setAppState('results');
    }
  };

  // Delete a chat session
  const deleteChatSession = (sessionId: string) => {
    const updatedSessions = chatSessions.filter(s => s.id !== sessionId);
    setChatSessions(updatedSessions);
    localStorage.setItem('chat_sessions', JSON.stringify(updatedSessions));
  };

  // Check if user is already logged in
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const user = await account.get();
      if (user) {
        // Get email from user object or localStorage
        const userEmail = user.email || localStorage.getItem('user_email') || 'user@example.com';
        // Only use stored custom name if it exists, otherwise leave empty
        const customName = localStorage.getItem('user_custom_name');
        const userName = customName || '';
        
        setUsername(userName);
        setDisplayName(userName);
        setEmail(userEmail);
        setAppState('home');
      }
    } catch (err) {
      // User not logged in, stay on auth page
      console.log('No active session');
      setAppState('auth');
    }
  };

  const handleSignUp = async (email: string, password: string) => {
    try {
      setError('');
      // Create account
      await account.create(ID.unique(), email, password);
      
      // Auto login after signup
      await account.createEmailPasswordSession(email, password);
      
      // Don't set username automatically - let user add it
      setUsername('');
      setDisplayName('');
      setEmail(email);
      
      // Store email but not name
      localStorage.setItem('user_email', email);
      
      // Start the flow: loading -> skeleton -> home
      setAppState('loading');
      
      setTimeout(() => {
        setAppState('skeleton');
        setTimeout(() => {
          setAppState('home');
        }, 3000);
      }, 2500);
    } catch (err: any) {
      setError(err.message || 'Sign up failed');
      console.error('Sign up error:', err);
    }
  };

  const handleSignIn = async (email: string, password: string) => {
    try {
      setError('');
      // Login
      await account.createEmailPasswordSession(email, password);
      
      // Check if user has a custom name stored
      const customName = localStorage.getItem('user_custom_name') || '';
      setUsername(customName);
      setDisplayName(customName);
      setEmail(email);
      
      // Store email
      localStorage.setItem('user_email', email);
      
      // Start the flow: loading -> skeleton -> home
      setAppState('loading');
      
      setTimeout(() => {
        setAppState('skeleton');
        setTimeout(() => {
          setAppState('home');
        }, 3000);
      }, 2500);
    } catch (err: any) {
      setError(err.message || 'Sign in failed');
      console.error('Sign in error:', err);
    }
  };

  const handleGoogleAuth = async () => {
    try {
      setError('');
      // Get the current URL origin for redirect
      const successUrl = `${window.location.origin}/auth/callback`;
      const failureUrl = `${window.location.origin}/?error=oauth_failed`;
      
      // Initiate Google OAuth
      account.createOAuth2Session(
        'google' as any, // Appwrite OAuth provider
        successUrl,
        failureUrl
      );
    } catch (err: any) {
      setError(err.message || 'Google sign-in failed');
      console.error('Google auth error:', err);
    }
  };

  const handleLogout = async () => {
    try {
      await account.deleteSession('current');
      
      // Reset theme to light mode on logout
      localStorage.setItem('theme', 'light');
      document.documentElement.classList.remove('dark');
      
      // Clear user data from localStorage
      localStorage.removeItem('user_email');
      localStorage.removeItem('user_name');
      localStorage.removeItem('user_custom_name');
      
      setAppState('auth');
      setUsername('');
      setEmail('user@example.com');
      setChatHistory([]);
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  const handleSearch = async (query: string) => {
    try {
      // Store the query
      setCurrentQuery(query);
      
      // Add user message to history immediately
      const userMessage = { role: 'user' as const, content: query, timestamp: new Date().toISOString() };
      setChatHistory(prev => [...prev, userMessage]);
      
      // Show results page immediately (loading state will be handled by UI if needed, or we can add a temporary loading message)
      setAppState('results');
      
      // Call backend API
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ 
          message: query,
          history: chatHistory // Pass current history to backend
        }),
      });

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = { message: await response.text() };
        }
        console.error('API Error:', response.status, errorData);
        throw new Error(errorData.message || `API returned ${response.status}`);
      }

      const data = await response.json();
      console.log('API Response:', data);
      
      // Extract the actual response from the backend structure
      const aiResponseContent = data.success && data.data ? data.data.content : data.message || JSON.stringify(data);
      
      // Add AI response to history
      setChatHistory(prev => [
        ...prev, 
        { 
          role: 'ai', 
          content: aiResponseContent, 
          timestamp: data.data?.timestamp || new Date().toISOString() 
        }
      ]);
      
    } catch (error: any) {
      console.error('Search error:', error);
      
      // Create a user-friendly error message
      let errorMessage = 'Failed to connect to backend API. ';
      if (error.message.includes('CORS')) {
        errorMessage = 'CORS Error: Backend needs to allow http://localhost:3000. Current allowed origin is http://127.0.0.1:5500';
      } else if (error.message.includes('404')) {
        errorMessage += 'Backend server not found. Make sure it\'s running on http://localhost:8080';
      } else if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
        errorMessage = 'Cannot reach backend server. Make sure it\'s running on http://localhost:8080 and CORS is configured for http://localhost:3000';
      } else {
        errorMessage += error.message;
      }
      
      // Add error message to history
      setChatHistory(prev => [
        ...prev,
        {
          role: 'ai',
          content: errorMessage,
          error: true,
          details: error.message
        }
      ]);
    }
  };

  const handleHomeClick = () => {
    setAppState('home');
  };

  const handleSettingsClick = () => {
    setAppState('settings');
  };

  const handlePersonalizationClick = () => {
    setAppState('personalization');
  };

  const handleNameUpdate = (name: string) => {
    setDisplayName(name);
    setUsername(name);
    // Store custom name in localStorage
    localStorage.setItem('user_custom_name', name);
  };

  const handleEmailUpdate = (newEmail: string) => {
    setEmail(newEmail);
    // Store email in localStorage
    localStorage.setItem('user_email', newEmail);
  };

  const handlePersonalizationSave = (data: { displayName: string; language: string }) => {
    setDisplayName(data.displayName);
    setUsername(data.displayName);
    // Save language preference here if needed
    setAppState('home');
  };

  const handleHelpClick = () => {
    setAppState('help');
  };

  const handleLogoClick = () => {
    // Save current chat session before starting new one
    saveCurrentChatSession();
    setAppState('home');
    setChatHistory([]);
    setCurrentQuery('');
  };

  return (
    <AnimatePresence mode="wait">
      {appState === 'auth' && (
        <div key="auth" className="flex min-h-screen">
          {/* Left side - Gradient Background */}
          <div className="hidden lg:flex lg:w-1/2 relative">
            <GradientBackground />
          </div>

          {/* Right side - Auth Forms */}
          <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-white">
            {error && (
              <div className="absolute top-4 right-4 bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-400 px-4 py-3 rounded">
                {error}
              </div>
            )}
            <AnimatePresence mode="wait">
              {isSignUp ? (
                <SignUpForm
                  key="signup"
                  onToggle={() => setIsSignUp(false)}
                  onSubmit={handleSignUp}
                  onGoogleAuth={handleGoogleAuth}
                />
              ) : (
                <SignInForm
                  key="signin"
                  onToggle={() => setIsSignUp(true)}
                  onSubmit={handleSignIn}
                  onGoogleAuth={handleGoogleAuth}
                />
              )}
            </AnimatePresence>
          </div>
        </div>
      )}

      {appState === 'loading' && <LoadingScreen key="loading" />}

      {appState === 'skeleton' && <SkeletonLoader key="skeleton" />}

      {appState === 'home' && (
        <HomePage
          key="home"
          onSearch={handleSearch}
          username={displayName}
          email={email}
          onLogout={handleLogout}
          onSettingsClick={handleSettingsClick}
          onNameUpdate={handleNameUpdate}
          onPersonalizationClick={handlePersonalizationClick}
          onHelpClick={handleHelpClick}
          onEmailUpdate={handleEmailUpdate}
        />
      )}

      {appState === 'results' && (
        <ResultsPage
          key="results"
          onSearch={handleSearch}
          username={displayName}
          email={email}
          onLogout={handleLogout}
          onHomeClick={handleHomeClick}
          onSettingsClick={handleSettingsClick}
          onPersonalizationClick={handlePersonalizationClick}
          onHelpClick={handleHelpClick}
          onEmailUpdate={handleEmailUpdate}
          chatHistory={chatHistory}
          searchQuery={currentQuery}
          onLogoClick={handleLogoClick}
          chatSessions={chatSessions}
          onRestoreSession={restoreChatSession}
          onDeleteSession={deleteChatSession}
        />
      )}

      {appState === 'settings' && (
        <SettingsPage
          key="settings"
          username={displayName}
          email={email}
          onHomeClick={handleHomeClick}
          onLogout={handleLogout}
          onLogoClick={handleLogoClick}
          chatSessions={chatSessions}
          onRestoreSession={restoreChatSession}
          onDeleteSession={deleteChatSession}
        />
      )}

      {appState === 'personalization' && (
        <PersonalizationPage
          key="personalization"
          username={displayName}
          email={email}
          onHomeClick={handleHomeClick}
          onSettingsClick={handleSettingsClick}
          onSave={handlePersonalizationSave}
          onLogoClick={handleLogoClick}
          chatSessions={chatSessions}
          onRestoreSession={restoreChatSession}
          onDeleteSession={deleteChatSession}
        />
      )}

      {appState === 'help' && (
        <HelpPage 
          key="help" 
          onHomeClick={handleHomeClick} 
          onSettingsClick={handleSettingsClick} 
          onLogoClick={handleLogoClick}
          chatSessions={chatSessions}
          onRestoreSession={restoreChatSession}
          onDeleteSession={deleteChatSession}
        />
      )}
    </AnimatePresence>
  );
}
