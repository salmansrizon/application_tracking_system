'use client';
import React, { useEffect, useState } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import JobCard from '@/components/jobs/JobCard';
import { getJobs, deleteJob as apiDeleteJob, JobApplication } from '@/services/jobService';
import Link from 'next/link';

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobApplication[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getJobs();
      setJobs(data);
    } catch (err) {
      console.error("Failed to fetch jobs:", err);
      setError("Failed to load job applications. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleDeleteJob = async (id: string) => {
    try {
      await apiDeleteJob(id);
      setJobs(prevJobs => prevJobs.filter(job => job.id !== id));
    } catch (err) {
      console.error("Failed to delete job:", err);
      setError("Failed to delete job application. Please try again.");
      // Optionally, re-fetch jobs or show more specific error handling
    }
  };

  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800">My Job Applications</h1>
          <Link href="/jobs/new" className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded-lg shadow-md transition-colors">
            Add New Application
          </Link>
        </div>

        {isLoading && <p className="text-center text-gray-600">Loading applications...</p>}
        {error && <p className="text-center text-red-500 bg-red-100 p-3 rounded-md">{error}</p>}

        {!isLoading && !error && jobs.length === 0 && (
          <p className="text-center text-gray-600 text-lg">You haven't added any job applications yet.</p>
        )}

        {!isLoading && !error && jobs.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {jobs.map(job => (
              <JobCard key={job.id} job={job} onDelete={handleDeleteJob} />
            ))}
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
