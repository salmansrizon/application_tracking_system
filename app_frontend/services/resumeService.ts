import apiClient from './apiClient';
import { z } from 'zod';

// Schema for resume metadata (matching ResumeMetadata from backend)
export const ResumeMetadataSchema = z.object({
  id: z.string().uuid(),
  filename: z.string().nullable().optional(),
  content_hash: z.string().nullable().optional(),
  storage_path: z.string().nullable().optional(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
});
export type ResumeMetadata = z.infer<typeof ResumeMetadataSchema>;

// Schema for the full resume data, including raw_text (matching ResumeRead from backend)
export const ResumeSchema = ResumeMetadataSchema.extend({
  user_id: z.string().uuid(),
  raw_text: z.string().nullable().optional(),
});
export type ResumeData = z.infer<typeof ResumeSchema>;


// Schema for the analysis request (matching ResumeAnalysisRequest from backend)
export const ResumeAnalysisRequestSchema = z.object({
  resume_id: z.string().uuid().optional(),
  resume_text: z.string().optional(),
  job_description_text: z.string().min(1, "Job description cannot be empty"),
});
export type ResumeAnalysisRequestData = z.infer<typeof ResumeAnalysisRequestSchema>;

// Schema for the analysis result (matching LLMAnalysisResult / ResumeAnalysisResponse from backend)
export const LLMAnalysisResultSchema = z.object({
  match_score: z.number().int().min(0).max(100),
  missing_keywords: z.array(z.string()),
  strength_summary: z.string(),
  improvement_suggestions: z.array(z.string()),
  ats_compatibility_check: z.string(),
});
export type LLMAnalysisResult = z.infer<typeof LLMAnalysisResultSchema>;


export const uploadResume = async (file: File): Promise<ResumeData> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/resumes/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return ResumeSchema.parse(response.data); // Validate and parse with full schema
};

export const listResumes = async (): Promise<ResumeMetadata[]> => {
  const response = await apiClient.get('/resumes/');
  return z.array(ResumeMetadataSchema).parse(response.data);
};

export const getResumeDetails = async (resumeId: string): Promise<ResumeData> => {
  const response = await apiClient.get(\`/resumes/\${resumeId}\`);
  return ResumeSchema.parse(response.data);
};

export const analyzeResume = async (data: ResumeAnalysisRequestData): Promise<LLMAnalysisResult> => {
  const response = await apiClient.post('/resumes/analyze', data);
  return LLMAnalysisResultSchema.parse(response.data);
};

export const deleteResume = async (resumeId: string): Promise<void> => {
  await apiClient.delete(\`/resumes/\${resumeId}\`);
};
