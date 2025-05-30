'use client';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import React, { useEffect, useState } from 'react';
import { getJobs, JobApplication } from '@/services/jobService'; // Assuming JobApplication type is exported

export default function DashboardPage() {
  const { user } = useAuth();
  const [totalJobs, setTotalJobs] = useState<number | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      if (!user) return; // Only fetch if user is loaded

      setIsLoadingStats(true);
      setStatsError(null);
      try {
        const jobs = await getJobs(); // Fetches jobs for the current user via apiClient
        setTotalJobs(jobs.length);
      } catch (error) {
        console.error("Failed to fetch job stats:", error);
        setStatsError("Could not load application statistics.");
      } finally {
        setIsLoadingStats(false);
      }
    };

    // Only fetch stats if the user is authenticated and loaded.
    // The ProtectedRoute component handles redirecting if not authenticated.
    // isLoading check from useAuth() might also be useful here if user object could be null during initial auth check.
    if (user) {
        fetchStats();
    } else {
        // If user is null and not loading (checked by ProtectedRoute essentially),
        // then no need to fetch stats. Or handle as per ProtectedRoute behavior.
        // For simplicity, fetchStats has its own user check.
    }
  }, [user]); // Re-fetch if user changes (e.g., on login)

  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">
          Welcome to your Dashboard, {user?.email?.split('@')[0] || 'User'}!
        </h1>
        <p className="text-lg text-gray-600 mb-8">Here's a quick overview of your job search progress.</p>

        {/* Stats Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-10">
          <div className="bg-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow">
            <h2 className="text-xl font-semibold text-gray-700 mb-2">Total Applications</h2>
            {isLoadingStats && <p className="text-3xl font-bold text-indigo-600 animate-pulse">Loading...</p>}
            {statsError && <p className="text-red-500">{statsError}</p>}
            {!isLoadingStats && totalJobs !== null && (
              <p className="text-5xl font-bold text-indigo-600">{totalJobs}</p>
            )}
            {!isLoadingStats && totalJobs === null && !statsError && (
                 <p className="text-3xl font-bold text-indigo-600">-</p>
            )}
          </div>
          {/* Placeholder for more stats cards - e.g., Interviews, Offers */}
          <div className="bg-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow">
            <h2 className="text-xl font-semibold text-gray-700 mb-2">Interviews Scheduled</h2>
            <p className="text-5xl font-bold text-green-600">0</p> {/* Placeholder */}
            <p className="text-sm text-gray-500 mt-1">Coming soon!</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow">
            <h2 className="text-xl font-semibold text-gray-700 mb-2">Offers Received</h2>
            <p className="text-5xl font-bold text-yellow-500">0</p> {/* Placeholder */}
            <p className="text-sm text-gray-500 mt-1">Coming soon!</p>
          </div>
        </div>

        {/* Quick Actions Section */}
        <div className="mb-10">
          <h2 className="text-2xl font-semibold text-gray-700 mb-4">Quick Actions</h2>
          <div className="flex flex-wrap gap-4">
            <Link href="/jobs/new" className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-6 rounded-lg shadow-md transition-colors text-center sm:w-auto w-full">
              Add New Application
            </Link>
            <Link href="/jobs" className="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg shadow-md transition-colors text-center sm:w-auto w-full">
              View All Applications
            </Link>
            {/* Placeholder for future actions like "Resume Analyzer" or "Interview Prep" */}
            <Link href="#" className="bg-gray-500 hover:bg-gray-600 text-white font-semibold py-3 px-6 rounded-lg shadow-md transition-colors text-center sm:w-auto w-full opacity-50 cursor-not-allowed" title="Coming Soon!">
              Analyze Resume (Soon)
            </Link>
          </div>
        </div>

        {/* Placeholder for Recent Activity or Upcoming Deadlines */}
        <div>
          <h2 className="text-2xl font-semibold text-gray-700 mb-4">Upcoming Deadlines</h2>
          <div className="bg-white p-6 rounded-lg shadow">
            <p className="text-gray-600">No upcoming deadlines within the next 7 days.</p> {/* Placeholder */}
            <p className="text-sm text-gray-500 mt-2">Feature coming soon!</p>
          </div>
        </div>

      </div>
    </ProtectedRoute>
  );
}
