import apiClient from './apiClient';
import { z } from 'zod';

// Define Zod schemas for validation - can be shared or redefined from backend if needed
// These are for frontend form validation and expected API response shapes.
// Match these with your backend Pydantic schemas (job_schemas.py)

export const JobApplicationSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  company: z.string().min(1, "Company is required"),
  position: z.string().min(1, "Position is required"),
  status: z.string().min(1, "Status is required"),
  deadline: z.string().nullable().optional(), // Assuming string date 'YYYY-MM-DD'
  notes: z.string().nullable().optional(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
});

export type JobApplication = z.infer<typeof JobApplicationSchema>;

export const JobApplicationCreateSchema = z.object({
  company: z.string().min(1, "Company is required"),
  position: z.string().min(1, "Position is required"),
  status: z.string().optional(),
  deadline: z.string().nullable().optional(), // Keep as string for form, convert if needed
  notes: z.string().nullable().optional(),
});
export type JobApplicationCreateData = z.infer<typeof JobApplicationCreateSchema>;

export const JobApplicationUpdateSchema = JobApplicationCreateSchema.partial();
export type JobApplicationUpdateData = z.infer<typeof JobApplicationUpdateSchema>;


export const getJobs = async (): Promise<JobApplication[]> => {
  const response = await apiClient.get('/jobs/');
  return JobApplicationSchema.array().parse(response.data); // Validate response
};

export const getJobById = async (id: string): Promise<JobApplication> => {
  const response = await apiClient.get(\`/jobs/\${id}\`);
  return JobApplicationSchema.parse(response.data);
};

export const createJob = async (data: JobApplicationCreateData): Promise<JobApplication> => {
  const response = await apiClient.post('/jobs/', data);
  return JobApplicationSchema.parse(response.data);
};

export const updateJob = async (id: string, data: JobApplicationUpdateData): Promise<JobApplication> => {
  const response = await apiClient.put(\`/jobs/\${id}\`, data);
  return JobApplicationSchema.parse(response.data);
};

export const deleteJob = async (id: string): Promise<void> => {
  await apiClient.delete(\`/jobs/\${id}\`);
};
