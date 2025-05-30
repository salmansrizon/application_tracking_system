'use client';
import React, { useState, useEffect, useCallback } from 'react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import {
  uploadResume as apiUploadResume,
  listResumes as apiListResumes,
  analyzeResume as apiAnalyzeResume,
  deleteResume as apiDeleteResume,
  ResumeMetadata,
  LLMAnalysisResult,
  ResumeData
} from '@/services/resumeService';
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Schema for the analysis form
const AnalysisFormSchema = z.object({
  selected_resume_id: z.string().uuid().optional().nullable(), // Allow null or undefined for clearing
  job_description_text: z.string().min(50, "Job description should be at least 50 characters"),
});
type AnalysisFormInputs = z.infer<typeof AnalysisFormSchema>;

export default function ResumeCheckerPage() {
  const { isAuthenticated } = useAuth(); // Assuming useAuth provides this, or just rely on ProtectedRoute
  const [uploadedResumes, setUploadedResumes] = useState<ResumeMetadata[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [fetchResumesError, setFetchResumesError] = useState<string | null>(null);

  const [analysisResult, setAnalysisResult] = useState<LLMAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const { register, handleSubmit, watch, setValue, formState: { errors: formErrors } } = useForm<AnalysisFormInputs>({
    resolver: zodResolver(AnalysisFormSchema),
    defaultValues: { // Set default to null for controlled component if needed
        selected_resume_id: null,
    }
  });
  const selectedResumeId = watch('selected_resume_id');

  const fetchUserResumes = useCallback(async () => {
    // ProtectedRoute handles redirect if not authenticated.
    // If isAuthenticated is available from useAuth, it can be an additional check.
    setFetchResumesError(null);
    try {
      const resumes = await apiListResumes();
      setUploadedResumes(resumes);
    } catch (error) {
      console.error("Failed to fetch resumes:", error);
      setFetchResumesError("Could not load your saved resumes. Please try again later.");
    }
  }, []); // Removed isAuthenticated from dep array as ProtectedRoute handles it.

  useEffect(() => {
    fetchUserResumes();
  }, [fetchUserResumes]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setValue('selected_resume_id', null); // Clear selection if new file is chosen
    }
  };

  const handleUploadAndAnalyze = async (jobDescText: string) => {
    if (!selectedFile) {
      // This state should ideally not be reached if UI logic is correct (button disabled or different handler)
      setUploadError("Please select a resume file to upload for analysis.");
      return;
    }
    setIsUploading(true); // Indicates start of upload part
    setIsAnalyzing(true); // Overall process is analysis
    setUploadError(null);
    setAnalysisError(null);
    setAnalysisResult(null);

    try {
      const newResume: ResumeData = await apiUploadResume(selectedFile);
      setIsUploading(false); // Upload part finished
      setUploadedResumes(prev => [
        // Filter out any potential existing resume with the same ID before adding, though unlikely for new uploads
        ...prev.filter(r => r.id !== newResume.id),
        { // Convert ResumeData to ResumeMetadata for the list
            id: newResume.id,
            filename: newResume.filename,
            content_hash: newResume.content_hash,
            storage_path: newResume.storage_path,
            created_at: newResume.created_at,
            updated_at: newResume.updated_at,
        }]
      );
      setSelectedFile(null);
      setValue('selected_resume_id', newResume.id);

      const result = await apiAnalyzeResume({ resume_id: newResume.id, job_description_text: jobDescText });
      setAnalysisResult(result);
    } catch (error: any) {
      console.error("Upload or analysis failed:", error);
      const errorMsg = error.response?.data?.detail || "An error occurred during upload or analysis.";
      setUploadError(errorMsg);
      setAnalysisError(errorMsg); // Also set general analysis error
    } finally {
      setIsUploading(false); // Ensure both are false on completion/error
      setIsAnalyzing(false);
    }
  };

  const handleAnalyzeExisting = async (resumeId: string, jobDescText: string) => {
    setIsAnalyzing(true);
    setAnalysisError(null);
    setAnalysisResult(null);
    setUploadError(null); // Clear any previous upload error
    try {
      const result = await apiAnalyzeResume({ resume_id: resumeId, job_description_text: jobDescText });
      setAnalysisResult(result);
    } catch (error: any) {
      console.error("Analysis failed:", error);
      setAnalysisError(error.response?.data?.detail || "An error occurred during analysis.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const onSubmit: SubmitHandler<AnalysisFormInputs> = async (data) => {
    if (selectedFile) {
      await handleUploadAndAnalyze(data.job_description_text);
    } else if (data.selected_resume_id) {
      await handleAnalyzeExisting(data.selected_resume_id, data.job_description_text);
    } else {
      setAnalysisError("Please select an existing resume or upload a new one to analyze.");
    }
  };

  const handleDeleteResume = async (resumeId: string) => {
    if (window.confirm("Are you sure you want to delete this resume? This action cannot be undone.")) {
      try {
        await apiDeleteResume(resumeId);
        setUploadedResumes(prev => prev.filter(r => r.id !== resumeId));
        if (selectedResumeId === resumeId) {
          setValue('selected_resume_id', null); // Clear from form if deleted
        }
      } catch (error: any) {
        console.error("Failed to delete resume:", error);
        setFetchResumesError(error.response?.data?.detail || "Failed to delete resume. Please try again.");
      }
    }
  };

  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-8">Resume Checker</h1>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-8 bg-white p-8 shadow-xl rounded-lg">
          <div>
            <h2 className="text-2xl font-semibold text-gray-700 mb-4">1. Your Resume</h2>
            {fetchResumesError && <p className="text-red-500 bg-red-100 p-3 rounded-md mb-4">{fetchResumesError}</p>}

            {uploadedResumes.length > 0 && (
              <div className="mb-4">
                <label htmlFor="selected_resume_id" className="block text-sm font-medium text-gray-700 mb-1">
                  Select an existing resume:
                </label>
                <select
                  id="selected_resume_id"
                  {...register('selected_resume_id')}
                  onChange={(e) => {
                    setValue('selected_resume_id', e.target.value || null); // Set to null if ""
                    if (e.target.value) setSelectedFile(null);
                  }}
                  className="block w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">-- Or upload a new one below --</option>
                  {uploadedResumes.map(resume => (
                    <option key={resume.id} value={resume.id}>{resume.filename || `Resume ${resume.id.substring(0,8)}`}</option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label htmlFor="resume_file" className="block text-sm font-medium text-gray-700 mb-1">
                {uploadedResumes.length > 0 ? "Or upload a new resume (PDF or DOCX, max 5MB):" : "Upload your resume (PDF or DOCX, max 5MB):"}
              </label>
              <input
                type="file"
                id="resume_file"
                onChange={handleFileChange}
                accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
              />
              {selectedFile && <p className="text-sm text-gray-600 mt-1">Selected file: {selectedFile.name}</p>}
              {uploadError && <p className="text-red-500 text-sm mt-1">{uploadError}</p>}
            </div>
            {uploadedResumes.length > 0 && (
                <div className="mt-4 space-y-2">
                    <h3 className="text-md font-semibold">Your uploaded resumes:</h3>
                    <ul className="list-disc pl-5 text-sm">
                        {uploadedResumes.map(r => (
                            <li key={r.id} className="flex justify-between items-center py-1">
                                <span>{r.filename || `Resume ${r.id.substring(0,8)}`} (Uploaded: {new Date(r.created_at).toLocaleDateString()})</span>
                                <button type="button" onClick={() => handleDeleteResume(r.id)} className="text-red-500 hover:text-red-700 text-xs font-medium">Delete</button>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
          </div>

          <div>
            <h2 className="text-2xl font-semibold text-gray-700 mb-4">2. Job Description</h2>
            <label htmlFor="job_description_text" className="block text-sm font-medium text-gray-700 mb-1">
              Paste the full job description here:
            </label>
            <textarea
              id="job_description_text"
              {...register('job_description_text')}
              rows={10}
              className="block w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Paste the job description text here..."
            />
            {formErrors.job_description_text && <p className="text-red-500 text-sm mt-1">{formErrors.job_description_text.message}</p>}
          </div>

          <div>
            <button
              type="submit"
              disabled={isUploading || isAnalyzing || (!selectedFile && !selectedResumeId)}
              className="w-full flex justify-center py-3 px-6 border border-transparent rounded-md shadow-sm text-lg font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-60"
            >
              {isUploading ? 'Uploading...' : (isAnalyzing ? 'Analyzing...' : 'Analyze Resume')}
            </button>
          </div>
        </form>

        {(isAnalyzing && !analysisResult && !analysisError) && <p className="mt-8 text-center text-indigo-600 text-lg">Analyzing your resume, please wait...</p>}
        {analysisError && <p className="mt-8 text-center text-red-600 bg-red-100 p-4 rounded-md text-lg">{analysisError}</p>}

        {analysisResult && (
          <div className="mt-12 p-8 bg-gray-50 shadow-xl rounded-lg">
            <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">Analysis Result</h2>

            <div className="mb-6 p-6 bg-indigo-100 rounded-lg text-center">
              <h3 className="text-xl font-semibold text-indigo-800 mb-1">Overall Match Score</h3>
              <p className="text-7xl font-bold text-indigo-600">{analysisResult.match_score}<span className="text-3xl">%</span></p>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div className="p-6 bg-white rounded-lg shadow">
                <h3 className="text-xl font-semibold text-gray-700 mb-3">Strengths Summary</h3>
                <p className="text-gray-600 whitespace-pre-line">{analysisResult.strength_summary}</p>
              </div>

              <div className="p-6 bg-white rounded-lg shadow">
                <h3 className="text-xl font-semibold text-gray-700 mb-3">ATS Compatibility</h3>
                <p className="text-gray-600 whitespace-pre-line">{analysisResult.ats_compatibility_check}</p>
              </div>
            </div>

            <div className="mt-6 p-6 bg-white rounded-lg shadow">
              <h3 className="text-xl font-semibold text-gray-700 mb-3">Missing Keywords/Skills</h3>
              {analysisResult.missing_keywords.length > 0 ? (
                <ul className="list-disc list-inside text-gray-600 space-y-1">
                  {analysisResult.missing_keywords.map((keyword, index) => <li key={index}>{keyword}</li>)}
                </ul>
              ) : <p className="text-gray-600">No critical keywords seem to be missing. Good job!</p>}
            </div>

            <div className="mt-6 p-6 bg-white rounded-lg shadow">
              <h3 className="text-xl font-semibold text-gray-700 mb-3">Improvement Suggestions</h3>
              {analysisResult.improvement_suggestions.length > 0 ? (
                <ul className="list-disc list-inside text-gray-600 space-y-2">
                  {analysisResult.improvement_suggestions.map((suggestion, index) => <li key={index}>{suggestion}</li>)}
                </ul>
              ) : <p className="text-gray-600">No specific improvement suggestions at this moment. Your resume looks strong for this role!</p>}
            </div>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
