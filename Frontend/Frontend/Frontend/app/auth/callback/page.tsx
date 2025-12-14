'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Client, Account } from 'appwrite';
import LoadingScreen from '@/app/components/LoadingScreen';

const client = new Client()
  .setEndpoint(process.env.NEXT_PUBLIC_APPWRITE_ENDPOINT || 'https://cloud.appwrite.io/v1')
  .setProject(process.env.NEXT_PUBLIC_APPWRITE_PROJECT_ID || '');

const account = new Account(client);

export default function AuthCallback() {
  const router = useRouter();

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get the current user session (OAuth creates it automatically)
        const user = await account.get();
        
        if (user) {
          // Store user email but not name - let user add it manually
          localStorage.setItem('user_email', user.email);
          // Only use custom name if already set
          const customName = localStorage.getItem('user_custom_name');
          if (!customName) {
            // Don't auto-populate from Google name
            localStorage.removeItem('user_name');
          }
          
          // Wait a bit for the loading animation
          setTimeout(() => {
            // Redirect to home page (which will show results)
            router.push('/');
          }, 2500);
        }
      } catch (error) {
        console.error('OAuth callback error:', error);
        // Redirect to home with error
        router.push('/?error=oauth_failed');
      }
    };

    handleCallback();
  }, [router]);

  return <LoadingScreen />;
}
