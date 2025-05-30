'use client';
import React from 'react';
import { JobApplication } from '@/services/jobService'; // Use the type from service
import Link from 'next/link';

interface JobCardProps {
  job: JobApplication;
  onDelete: (id: string) => void;
}

const JobCard: React.FC<JobCardProps> = ({ job, onDelete }) => {
  const handleDelete = () => {
    if (window.confirm(\`Are you sure you want to delete the application for \${job.position} at \${job.company}?\`)) {
      onDelete(job.id);
    }
  };

  return (
    <div className="bg-white shadow-lg rounded-lg p-6 mb-6 transition-shadow hover:shadow-xl">
      <h3 className="text-2xl font-semibold text-indigo-700 mb-2">{job.position}</h3>
      <p className="text-lg text-gray-800 mb-1">{job.company}</p>
      <p className="text-sm text-gray-600 mb-3">Status: <span className="font-medium text-indigo-600">{job.status}</span></p>
      {job.deadline && (
        <p className="text-sm text-gray-500 mb-1">Deadline: {new Date(job.deadline).toLocaleDateString()}</p>
      )}
      {job.notes && (
        <p className="text-sm text-gray-500 mb-3">Notes: {job.notes}</p>
      )}
      <div className="mt-4 flex justify-end space-x-3">
        <Link href={\`/jobs/\${job.id}/edit\`} className="text-sm text-blue-600 hover:text-blue-800 font-medium">
          Edit
        </Link>
        <button
          onClick={handleDelete}
          className="text-sm text-red-600 hover:text-red-800 font-medium"
        >
          Delete
        </button>
      </div>
       <p className="text-xs text-gray-400 mt-2 text-right">Last updated: {new Date(job.updated_at).toLocaleDateString()}</p>
    </div>
  );
};

export default JobCard;
