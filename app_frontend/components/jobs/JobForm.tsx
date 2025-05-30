'use client';
import React from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { JobApplicationCreateSchema, JobApplicationCreateData, JobApplication } from '@/services/jobService';
import { useRouter } from 'next/navigation';

interface JobFormProps {
  onSubmit: (data: JobApplicationCreateData) => Promise<void>;
  initialData?: Partial<JobApplication>; // For pre-filling the form in edit mode
  isEditMode?: boolean;
  submitButtonText?: string;
  formError?: string | null;
}

const JobForm: React.FC<JobFormProps> = ({
  onSubmit,
  initialData = {},
  isEditMode = false,
  submitButtonText = 'Submit',
  formError
}) => {
  const router = useRouter();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<JobApplicationCreateData>({
    resolver: zodResolver(JobApplicationCreateSchema),
    defaultValues: {
      company: initialData.company || '',
      position: initialData.position || '',
      status: initialData.status || 'applied',
      deadline: initialData.deadline ? initialData.deadline.split('T')[0] : '', // Format for <input type="date">
      notes: initialData.notes || '',
    },
  });

  const handleFormSubmit: SubmitHandler<JobApplicationCreateData> = async (data) => {
    // Ensure deadline is either a valid date string or null if empty
    const payload = {
      ...data,
      deadline: data.deadline ? data.deadline : null,
    };
    await onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6 bg-white p-8 shadow-md rounded-lg">
      {formError && <p className="text-red-500 text-sm mb-4 text-center p-2 bg-red-100 rounded">{formError}</p>}
      <div>
        <label htmlFor="company" className="block text-sm font-medium text-gray-700">Company</label>
        <input id="company" {...register('company')} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
        {errors.company && <p className="text-red-500 text-xs mt-1">{errors.company.message}</p>}
      </div>

      <div>
        <label htmlFor="position" className="block text-sm font-medium text-gray-700">Position</label>
        <input id="position" {...register('position')} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
        {errors.position && <p className="text-red-500 text-xs mt-1">{errors.position.message}</p>}
      </div>

      <div>
        <label htmlFor="status" className="block text-sm font-medium text-gray-700">Status</label>
        <select id="status" {...register('status')} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
          <option value="wishlist">Wishlist</option>
          <option value="applied">Applied</option>
          <option value="interviewing">Interviewing</option>
          <option value="offer">Offer</option>
          <option value="rejected">Rejected</option>
          <option value="no_response">No Response</option>
        </select>
        {errors.status && <p className="text-red-500 text-xs mt-1">{errors.status.message}</p>}
      </div>

      <div>
        <label htmlFor="deadline" className="block text-sm font-medium text-gray-700">Deadline (Optional)</label>
        <input id="deadline" type="date" {...register('deadline')} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
        {errors.deadline && <p className="text-red-500 text-xs mt-1">{errors.deadline.message}</p>}
      </div>

      <div>
        <label htmlFor="notes" className="block text-sm font-medium text-gray-700">Notes (Optional)</label>
        <textarea id="notes" {...register('notes')} rows={4} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"></textarea>
        {errors.notes && <p className="text-red-500 text-xs mt-1">{errors.notes.message}</p>}
      </div>

      <div className="flex items-center justify-end space-x-3">
        <button type="button" onClick={() => router.back()} className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none">
          Cancel
        </button>
        <button type="submit" disabled={isSubmitting} className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50">
          {isSubmitting ? (isEditMode ? 'Updating...' : 'Creating...') : submitButtonText}
        </button>
      </div>
    </form>
  );
};

export default JobForm;
