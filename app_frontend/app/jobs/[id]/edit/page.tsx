'use client';
import React, { useEffect, useState } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import JobForm from '@/components/jobs/JobForm';
import { getJobById, updateJob, JobApplication, JobApplicationUpdateData } from '@/services/jobService';
import { useRouter, useParams } from 'next/navigation'; // useParams for App Router

export default function EditJobPage() {
  const router = useRouter();
  const params = useParams(); // { id: '...' }
  const id = params?.id as string; // Ensure id is string

  const [job, setJob] = useState<JobApplication | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null); // For fetching error
  const [formError, setFormError] = useState<string | null>(null); // For form submission error

  useEffect(() => {
    if (id) {
      setIsLoading(true);
      setError(null);
      getJobById(id)
        .then(data => {
          setJob(data);
        })
        .catch(err => {
          console.error("Failed to fetch job for editing:", err);
          setError("Failed to load job application details.");
        })
        .finally(() => setIsLoading(false));
    } else {
        setError("Job ID is missing.");
        setIsLoading(false);
    }
  }, [id]);

  const handleUpdateJob = async (data: JobApplicationUpdateData) => {
    if (!id) return;
    setFormError(null);
    try {
      await updateJob(id, data);
      router.push('/jobs'); // Redirect to jobs list on success
    } catch (err: any) {
      console.error("Failed to update job:", err);
      setFormError(err.response?.data?.detail || "Failed to update job application. Please try again.");
    }
  };

  if (isLoading) return <ProtectedRoute><div className="text-center p-10">Loading job details...</div></ProtectedRoute>;
  if (error) return <ProtectedRoute><div className="text-center text-red-500 p-10 bg-red-100 rounded">{error}</div></ProtectedRoute>;
  if (!job) return <ProtectedRoute><div className="text-center p-10">Job application not found.</div></ProtectedRoute>;

  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Edit Job Application</h1>
        <JobForm
          onSubmit={handleUpdateJob}
          initialData={job}
          isEditMode={true}
          submitButtonText="Update Application"
          formError={formError}
        />
      </div>
    </ProtectedRoute>
  );
}
