'use client';
import React, { useState } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import JobForm from '@/components/jobs/JobForm';
import { createJob, JobApplicationCreateData } from '@/services/jobService';
import { useRouter } from 'next/navigation';

export default function NewJobPage() {
  const router = useRouter();
  const [formError, setFormError] = useState<string | null>(null);

  const handleCreateJob = async (data: JobApplicationCreateData) => {
    setFormError(null);
    try {
      await createJob(data);
      router.push('/jobs'); // Redirect to jobs list on success
    } catch (err: any) {
      console.error("Failed to create job:", err);
      setFormError(err.response?.data?.detail || "Failed to create job application. Please try again.");
    }
  };

  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Add New Job Application</h1>
        <JobForm
          onSubmit={handleCreateJob}
          submitButtonText="Create Application"
          formError={formError}
        />
      </div>
    </ProtectedRoute>
  );
}
