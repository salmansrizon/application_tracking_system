import apiClient from './apiClient';
import { z } from 'zod'; // Using Zod for response validation

// Define the structure for individual questions based on backend's InterviewQuestion model
export const InterviewQuestionSchema = z.object({
  question: z.string(),
  category: z.string(), // e.g., "Behavioral", "Technical", "Situational"
  // star_hint: z.string().optional(), // If you add this to backend
});
export type InterviewQuestion = z.infer<typeof InterviewQuestionSchema>;

// Define the structure for the overall result (matching backend's InterviewPrepResult)
export const InterviewPrepResultSchema = z.object({
  generated_questions: z.array(InterviewQuestionSchema),
  preparation_tips: z.array(z.string()),
});
export type InterviewPrepResult = z.infer<typeof InterviewPrepResultSchema>;

// Define the structure for the request payload
export interface InterviewQuestionRequestData {
  resume_id?: string; // UUID string
  resume_text?: string;
  job_description_text: string;
}

export const generateInterviewQuestions = async (
  data: InterviewQuestionRequestData
): Promise<InterviewPrepResult> => {
  const response = await apiClient.post('/interview/generate-questions', data);
  // Validate the response data with Zod schema
  return InterviewPrepResultSchema.parse(response.data);
};
