### 🖥️ **FRONTEND-CONTEXT.md**

# Application Tracker System - Frontend Context

## Purpose
To provide an intuitive interface for:
1. Managing job applications
2. Uploading/resume analysis
3. Tracking progress against job descriptions
4. Interview preparation tools

## Key Features
- Dashboard with application overview
- Resume upload + instant feedback
- Job application tracker with filters
- Status update widgets
- Interview question generator

## Folder Structure
```
app/
├── components/ # Reusable UI components
│ ├── JobCard.tsx # Individual job application card
│ ├── ResumeUploader.tsx # Resume upload component
│ └── StatusBadge.tsx # Visual status indicator
├── pages/
│ ├── dashboard/ # Overview page
│ ├── tracker/ # Job application list
│ ├── resume-checker/ # Resume analysis interface
│ └── interview/ # Prep tools
├── services/ # API client
└── hooks/ # Custom React hooks
```

## 🎨 Components
### `ResumeChecker`
```
function ResumeChecker() {
  const [analysis, setAnalysis] = useState(null);
  
  const handleUpload = async (file) => {
    const resumeText = await extractTextFromPDF(file);
    const jobDescription = getCurrentJobDescription();
    
    const result = await api.post('/resume/analyze', { resumeText, jobDescription });
    setAnalysis(result.data);
  };
}
```

## Pages
1. Dashboard :
    - Summary cards (total apps, pending deadlines)
    - Quick actions (add job, upload resume)
2. Tracker :
    - Table view of applications with filters
    - Status change dropdowns
3. Resume Checker :
    - Drag-and-drop upload
    - Side-by-side comparison with job description
    - Improvement suggestions


## Integrations
    - Backend API : Axios-based services for /jobs, /resume, etc.
    - Supabase Auth : User session management
    - React Hook Form : Form validation
    - TailwindCSS : Responsive styling


## Enhancv-Inspired Features
1. Resume Checklist :
    - Required elements check (contact info, experience, skills)
    - Percentage completeness indicator
2. JD Match Analyzer :
    - Keyword overlap visualization
    - Skills gap identification
3. Interview Prep :
    - LLM-generated questions based on job description
    - STAR method templates


---

### ✅ Implementation Notes
1. **LLM Prompt Optimization**:
   - Use few-shot prompting for consistent resume analysis format
   - Add bias detection in skill matching

2. **Local Development**:
   ```bash
   # Test resume analysis
   curl -X POST /resume/analyze \
     -H "Content-Type: application/json" \
     -d '{"resume_text":"...", "job_description":"..."}'

## Create jobs table
```
CREATE TABLE jobs (
  id UUID PRIMARY KEY,
  company TEXT NOT NULL,
  position TEXT NOT NULL,
  deadline DATE,
  user_id UUID REFERENCES auth.users(id)
);
```