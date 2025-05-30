'use client';
import React, { useState, useEffect, useCallback } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import { listResumes as apiListResumes, ResumeMetadata } from '@/services/resumeService'; // To list resumes
import {
  generateInterviewQuestions as apiGenerateQuestions,
  InterviewPrepResult,
  InterviewQuestionRequestData
} from '@/services/interviewService'; // The new service
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Link from 'next/link'; // Added for linking to resume checker

// Schema for the interview prep form
const InterviewPrepFormSchema = z.object({
  selected_resume_id: z.string().uuid("Please select a valid resume.").optional().nullable(), // Allow null for placeholder
  job_description_text: z.string().min(50, "Job description should be at least 50 characters."),
});
type InterviewPrepFormInputs = z.infer<typeof InterviewPrepFormSchema>;

export default function InterviewPrepPage() {
  const { isAuthenticated } = useAuth(); // Or just rely on ProtectedRoute
  const [userResumes, setUserResumes] = useState<ResumeMetadata[]>([]);
  const [fetchResumesError, setFetchResumesError] = useState<string | null>(null);

  const [generatedResult, setGeneratedResult] = useState<InterviewPrepResult | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);

  const { register, handleSubmit, watch, formState: { errors: formErrors } } = useForm<InterviewPrepFormInputs>({
    resolver: zodResolver(InterviewPrepFormSchema),
    defaultValues: {
        selected_resume_id: null, // Default to null for the select placeholder
    }
  });

  const fetchUserResumesList = useCallback(async () => {
    // ProtectedRoute should handle unauthenticated state.
    setFetchResumesError(null);
    try {
      const resumes = await apiListResumes();
      setUserResumes(resumes);
    } catch (error) {
      console.error("Failed to fetch user resumes:", error);
      setFetchResumesError("Could not load your saved resumes. Please ensure you are logged in or try again later.");
    }
  }, []); // Removed isAuthenticated as ProtectedRoute handles it

  useEffect(() => {
    fetchUserResumesList();
  }, [fetchUserResumesList]);

  const onSubmit: SubmitHandler<InterviewPrepFormInputs> = async (data) => {
    if (!data.selected_resume_id) {
      setGenerationError("Please select one of your resumes to generate questions.");
      return;
    }

    setIsGenerating(true);
    setGenerationError(null);
    setGeneratedResult(null);

    const requestPayload: InterviewQuestionRequestData = {
      resume_id: data.selected_resume_id,
      job_description_text: data.job_description_text,
    };

    try {
      const result = await apiGenerateQuestions(requestPayload);
      setGeneratedResult(result);
    } catch (error: any) {
      console.error("Interview question generation failed:", error);
      setGenerationError(error.response?.data?.detail || "An error occurred while generating questions.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-8">AI Interview Preparation</h1>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-8 bg-white p-8 shadow-xl rounded-lg mb-12">
          <div>
            <h2 className="text-2xl font-semibold text-gray-700 mb-4">1. Select Your Resume</h2>
            {fetchResumesError && <p className="text-red-500 bg-red-100 p-3 rounded-md mb-4">{fetchResumesError}</p>}

            {userResumes.length > 0 ? (
              <div>
                <label htmlFor="selected_resume_id" className="block text-sm font-medium text-gray-700 mb-1">
                  Choose one of your uploaded resumes:
                </label>
                <select
                  id="selected_resume_id"
                  {...register('selected_resume_id')}
                  className="block w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">-- Select a Resume --</option>
                  {userResumes.map(resume => (
                    <option key={resume.id} value={resume.id}>{resume.filename || \`Resume (\${resume.id.substring(0,8)}...)\`}</option>
                  ))}
                </select>
                {formErrors.selected_resume_id && <p className="text-red-500 text-sm mt-1">{formErrors.selected_resume_id.message}</p>}
              </div>
            ) : (
              <p className="text-gray-600">
                You don't have any uploaded resumes. Please go to the
                <Link href="/resume-checker" className="text-indigo-600 hover:underline ml-1">Resume Checker</Link>
                to upload one first.
              </p>
            )}
          </div>

          <div>
            <h2 className="text-2xl font-semibold text-gray-700 mb-4">2. Target Job Description</h2>
            <label htmlFor="job_description_text" className="block text-sm font-medium text-gray-700 mb-1">
              Paste the full job description:
            </label>
            <textarea
              id="job_description_text"
              {...register('job_description_text')}
              rows={12}
              className="block w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Paste the job description text here..."
            />
            {formErrors.job_description_text && <p className="text-red-500 text-sm mt-1">{formErrors.job_description_text.message}</p>}
          </div>

          <div>
            <button
              type="submit"
              disabled={isGenerating || userResumes.length === 0 || !watch('selected_resume_id')}
              className="w-full flex justify-center py-3 px-6 border border-transparent rounded-md shadow-sm text-lg font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-60"
            >
              {isGenerating ? 'Generating Questions...' : 'Generate Interview Questions'}
            </button>
          </div>
        </form>

        {(isGenerating && !generatedResult && !generationError) && <p className="mt-8 text-center text-indigo-600 text-lg">Generating questions, please wait...</p>}
        {generationError && <p className="mt-8 text-center text-red-600 bg-red-100 p-4 rounded-md text-lg">{generationError}</p>}

        {generatedResult && (
          <div className="mt-12 p-8 bg-gray-50 shadow-xl rounded-lg">
            <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">Your Interview Prep Plan</h2>

            <div className="mb-8">
              <h3 className="text-2xl font-semibold text-indigo-700 mb-4">Generated Questions:</h3>
              {generatedResult.generated_questions.length > 0 ? (
                <div className="space-y-6">
                  {generatedResult.generated_questions.map((q, index) => (
                    <div key={index} className="p-4 bg-white rounded-lg shadow">
                      <span className="inline-block bg-indigo-200 text-indigo-800 text-xs font-semibold px-2.5 py-0.5 rounded-full mb-2">
                        {q.category}
                      </span>
                      <p className="text-gray-700 text-lg">{q.question}</p>
                    </div>
                  ))}
                </div>
              ) : <p className="text-gray-600">No specific questions generated this time. Try refining the job description or resume.</p>}
            </div>

            <div>
              <h3 className="text-2xl font-semibold text-green-700 mb-4">Preparation Tips:</h3>
              {generatedResult.preparation_tips.length > 0 ? (
                <ul className="list-disc list-inside text-gray-700 space-y-3 bg-white p-6 rounded-lg shadow">
                  {generatedResult.preparation_tips.map((tip, index) => (
                    <li key={index} className="text-md">{tip}</li>
                  ))}
                </ul>
              ) : <p className="text-gray-600">No specific preparation tips provided for this combination.</p>}
            </div>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
