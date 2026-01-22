# Phase 6: React Frontend - Research

**Researched:** 2026-01-22
**Domain:** React + TypeScript + Vite frontend for FastAPI backend
**Confidence:** HIGH

## Summary

This research investigates the technology stack and patterns needed to build a React frontend for the Cosmograph document-to-knowledge-graph service. The frontend must integrate with the existing FastAPI backend (Phase 5), providing file upload, extraction progress display, graph visualization embedding, and download capabilities.

The standard approach is Vite 7.x with React 18/19 and TypeScript, using native browser APIs for file upload and SSE for progress streaming. The generated HTML visualization is self-contained with embedded D3.js, so the frontend should display it via iframe rather than reimplement the graph rendering.

**Primary recommendation:** Use Vite + React + TypeScript with minimal dependencies. Prefer native FormData API for file uploads, native EventSource for SSE progress, and iframe embedding for the existing D3.js visualization. Keep styling simple with CSS modules or inline styles rather than heavy frameworks.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Vite | 7.3+ | Build tool & dev server | Official React recommendation, fast HMR, native ESM |
| React | 18.x/19.x | UI framework | Iyeska standard stack |
| TypeScript | 5.x | Type safety | Iyeska standard stack, catches errors at compile time |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react-dropzone | 14.x | Drag & drop file upload | If native DnD API proves insufficient |
| @ramonak/react-progress-bar | 5.x | Progress visualization | Only if custom CSS insufficient |

### Explicitly NOT Needed
| Library | Reason Not Needed |
|---------|-------------------|
| axios | Native fetch sufficient for this use case |
| D3.js | Graph already rendered in self-contained HTML |
| react-query/SWR | Simple API calls don't need caching layer |
| Redux/Zustand | Local state sufficient for single-page flow |
| Tailwind CSS | Minimal UI doesn't justify build complexity |
| shadcn/ui | Over-engineered for "functional, not over-designed" requirement |

**Installation:**
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/
├── src/
│   ├── components/       # UI components
│   │   ├── FileUpload.tsx
│   │   ├── ExtractionOptions.tsx
│   │   ├── ProgressDisplay.tsx
│   │   ├── GraphPreview.tsx
│   │   ├── DownloadButtons.tsx
│   │   └── ErrorDisplay.tsx
│   ├── hooks/            # Custom hooks
│   │   ├── useExtraction.ts
│   │   └── useProgress.ts
│   ├── services/         # API abstraction
│   │   └── api.ts
│   ├── types/            # TypeScript types
│   │   └── index.ts
│   ├── App.tsx           # Main app component
│   ├── App.css           # Global styles
│   └── main.tsx          # Entry point
├── public/
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

### Pattern 1: API Service Abstraction
**What:** Centralize all API calls in a service layer with typed responses.
**When to use:** Always for API interactions.
**Example:**
```typescript
// Source: Best practices from React architecture guides
// services/api.ts
const API_BASE = '/api';

interface JobResponse {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  total: number;
  error: string | null;
}

export async function createExtraction(
  files: File[],
  extractor: string,
  title: string,
  llmConfirmed: boolean
): Promise<JobResponse> {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  formData.append('extractor', extractor);
  formData.append('title', title);
  formData.append('llm_confirmed', String(llmConfirmed));

  // IMPORTANT: Do NOT set Content-Type header - browser sets it with boundary
  const response = await fetch(`${API_BASE}/extract`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Extraction failed');
  }

  return response.json();
}
```

### Pattern 2: SSE Progress Hook
**What:** Custom hook that manages EventSource connection for real-time progress.
**When to use:** For the extraction progress display.
**Example:**
```typescript
// Source: Native EventSource API patterns
// hooks/useProgress.ts
import { useEffect, useState, useCallback } from 'react';

interface ProgressState {
  status: string;
  progress: number;
  total: number;
  isComplete: boolean;
  error: string | null;
}

export function useProgress(jobId: string | null) {
  const [state, setState] = useState<ProgressState>({
    status: 'pending',
    progress: 0,
    total: 0,
    isComplete: false,
    error: null,
  });

  useEffect(() => {
    if (!jobId) return;

    const eventSource = new EventSource(`/api/extract/${jobId}/progress`);

    eventSource.addEventListener('progress', (event) => {
      const data = JSON.parse(event.data);
      setState(prev => ({
        ...prev,
        status: data.status,
        progress: data.progress,
        total: data.total,
      }));
    });

    eventSource.addEventListener('complete', () => {
      setState(prev => ({ ...prev, isComplete: true }));
      eventSource.close();
    });

    eventSource.addEventListener('error', (event) => {
      // SSE error event - check if it's a data event or connection error
      if (event instanceof MessageEvent) {
        const data = JSON.parse(event.data);
        setState(prev => ({ ...prev, error: data.error }));
      }
      eventSource.close();
    });

    eventSource.onerror = () => {
      // Connection error - EventSource will auto-reconnect
      console.error('SSE connection error');
    };

    return () => eventSource.close();
  }, [jobId]);

  return state;
}
```

### Pattern 3: Iframe Embedding for D3.js Visualization
**What:** Display the self-contained HTML visualization via iframe.
**When to use:** For the graph preview after extraction completes.
**Example:**
```typescript
// Source: D3.js embedding patterns
// components/GraphPreview.tsx
interface GraphPreviewProps {
  jobId: string;
}

export function GraphPreview({ jobId }: GraphPreviewProps) {
  // Use blob URL from downloaded HTML for iframe src
  const htmlUrl = `/api/download/${jobId}`;

  return (
    <div style={{ flex: 1, minHeight: '400px' }}>
      <iframe
        src={htmlUrl}
        style={{ width: '100%', height: '100%', border: 'none' }}
        title="Knowledge Graph Visualization"
      />
    </div>
  );
}
```

### Pattern 4: File Upload with Drag & Drop
**What:** Native HTML5 drag and drop with file input fallback.
**When to use:** For the upload component.
**Example:**
```typescript
// Source: Native browser drag and drop API
// components/FileUpload.tsx
import { useState, DragEvent, ChangeEvent } from 'react';

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
}

export function FileUpload({ onFilesSelected }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    onFilesSelected(files);
  };

  const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      onFilesSelected(Array.from(e.target.files));
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      style={{
        border: `2px dashed ${isDragging ? '#4fc3f7' : '#666'}`,
        borderRadius: '8px',
        padding: '40px',
        textAlign: 'center',
        background: isDragging ? 'rgba(79, 195, 247, 0.1)' : 'transparent',
        transition: 'all 0.2s',
      }}
    >
      <p>Drag & drop files here, or</p>
      <input
        type="file"
        multiple
        onChange={handleFileInput}
        style={{ marginTop: '10px' }}
      />
    </div>
  );
}
```

### Anti-Patterns to Avoid
- **Setting Content-Type header for FormData:** Browser must set it with boundary. Let fetch handle it.
- **Re-implementing D3.js graph in React:** The HTML is self-contained. Use iframe, don't rebuild.
- **Using heavyweight state management:** Local useState sufficient for this single-flow app.
- **Over-designing UI:** Requirements explicitly say "minimal, functional CSS (not over-designed)".

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File drag & drop | Custom drag/drop logic | Native HTML5 DnD API | Browser handles edge cases |
| SSE handling | Custom XHR streaming | Native EventSource | Handles reconnection automatically |
| Progress bar | Complex animation logic | CSS width transition | Simple, performant |
| Form data encoding | Manual multipart encoding | FormData API | Browser handles boundary correctly |
| Graph visualization | React D3 integration | Iframe embedding | HTML is already self-contained |

**Key insight:** The backend generates self-contained HTML with embedded D3.js and data. Rebuilding the graph in React would duplicate effort and add complexity. Iframe embedding is the correct pattern here.

## Common Pitfalls

### Pitfall 1: Setting Content-Type Header for File Upload
**What goes wrong:** File upload fails or files are corrupted.
**Why it happens:** Setting `Content-Type: multipart/form-data` manually prevents browser from adding the boundary parameter.
**How to avoid:** Never set Content-Type when using FormData with fetch. Browser sets it automatically with correct boundary.
**Warning signs:** "Invalid multipart" errors, empty files on server.

### Pitfall 2: Not Handling SSE Connection Lifecycle
**What goes wrong:** Memory leaks, stale connections, missing progress updates.
**Why it happens:** EventSource not closed when component unmounts or job completes.
**How to avoid:** Close EventSource in useEffect cleanup function. Handle 'complete' and 'error' events to close early.
**Warning signs:** Multiple progress streams running, browser connection limits hit.

### Pitfall 3: Using react-dropzone Without Need
**What goes wrong:** Extra bundle size, potential conflicts, version churn.
**Why it happens:** Developers default to libraries instead of native APIs.
**How to avoid:** Start with native DnD. Only add library if specific feature needed (accessibility, image preview, validation).
**Warning signs:** Bundle analyzer shows large chunk for simple drag/drop.

### Pitfall 4: LLM Extraction Without Confirmation UI
**What goes wrong:** API rejects request with 400 error about missing llm_confirmed.
**Why it happens:** Backend requires explicit confirmation for data sovereignty.
**How to avoid:** When extractor="llm", show confirmation dialog before submitting. Set llm_confirmed=true only after user confirms.
**Warning signs:** "LLM extraction requires llm_confirmed=true" error message.

### Pitfall 5: Vite Proxy Not Configured
**What goes wrong:** CORS errors in development, API calls fail.
**Why it happens:** Frontend on :5173 tries to call backend on :8000.
**How to avoid:** Configure server.proxy in vite.config.ts to forward /api to backend.
**Warning signs:** "Cross-Origin Request Blocked" in console.

## Code Examples

Verified patterns from official sources:

### Vite Configuration with Proxy
```typescript
// Source: https://vite.dev/config/server-options.html
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

### TypeScript Types Matching Backend Schemas
```typescript
// Source: Backend schemas.py
// types/index.ts
export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type ExtractorType = 'auto' | 'legal' | 'text' | 'generic' | 'pdf' | 'llm';

export interface JobResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  total: number;
  created_at: string;
  error: string | null;
}

export interface GraphResponse {
  title: string;
  nodes: Array<{
    id: string;
    label: string;
    category: string;
    description?: string;
  }>;
  edges: Array<{
    source: string;
    target: string;
    label: string;
  }>;
  stats: {
    nodes: number;
    edges: number;
  };
}
```

### Simple Progress Bar with CSS
```typescript
// Source: React progress bar best practices
// components/ProgressDisplay.tsx
interface ProgressDisplayProps {
  progress: number;
  total: number;
  status: string;
}

export function ProgressDisplay({ progress, total, status }: ProgressDisplayProps) {
  const percent = total > 0 ? Math.round((progress / total) * 100) : 0;

  return (
    <div style={{ marginBottom: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
        <span>{status === 'processing' ? `Processing file ${progress} of ${total}` : status}</span>
        <span>{percent}%</span>
      </div>
      <div style={{
        width: '100%',
        height: '8px',
        background: '#333',
        borderRadius: '4px',
        overflow: 'hidden',
      }}>
        <div style={{
          width: `${percent}%`,
          height: '100%',
          background: '#4fc3f7',
          transition: 'width 0.3s ease',
        }} />
      </div>
    </div>
  );
}
```

### Traefik Configuration for cosmograph.localhost
```yaml
# Source: Traefik documentation
# Add to Iyeska traefik docker-compose or file provider
# Dynamic configuration for cosmograph frontend
http:
  routers:
    cosmograph-frontend:
      rule: "Host(`cosmograph.localhost`)"
      service: cosmograph-frontend
      entrypoints:
        - web

  services:
    cosmograph-frontend:
      loadBalancer:
        servers:
          - url: "http://host.docker.internal:5173"

# Or via Docker Compose labels if running frontend in container:
# labels:
#   - "traefik.http.routers.cosmograph.rule=Host(`cosmograph.localhost`)"
#   - "traefik.http.services.cosmograph.loadbalancer.server.port=5173"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Create React App | Vite | 2022-2023 | Faster dev server, smaller bundle |
| React.FC type | Plain function components | TypeScript 5.1+ | Simpler, better generic support |
| Class components | Function + hooks | React 16.8+ | Standard practice |
| axios for everything | Native fetch | ES2017+ | Less dependencies, browser-native |
| WebSocket for updates | SSE for server-push | N/A | Simpler for unidirectional streaming |

**Deprecated/outdated:**
- Create React App: No longer recommended, use Vite
- React.FC: Optional, prefer `function Component(props: Props)` syntax
- componentDidMount/etc: Use useEffect hooks

## Open Questions

Things that couldn't be fully resolved:

1. **Traefik exact configuration location**
   - What we know: Iyeska uses Traefik at ~/terminal_projects/claude_code/traefik
   - What's unclear: Exact docker-compose structure for adding cosmograph route
   - Recommendation: Check existing traefik config during planning, add label or file provider entry

2. **React 18 vs React 19**
   - What we know: Vite 7.x template uses React 18 by default, React 19 is available
   - What's unclear: Whether to upgrade to React 19 for this project
   - Recommendation: Stay with React 18 (stable), React 19 adds complexity without clear benefit here

3. **Production build deployment**
   - What we know: Phase 7 handles deployment to 192.168.11.20
   - What's unclear: How frontend build will be served (nginx, FastAPI static files, or separate PM2 process)
   - Recommendation: Plan for static file serving; decision deferred to Phase 7

## Sources

### Primary (HIGH confidence)
- [Vite Official Documentation](https://vite.dev/guide/) - Scaffolding, configuration, server options
- [Vite Server Options](https://vite.dev/config/server-options.html) - Proxy configuration syntax
- Backend source code (src/cosmograph/api/) - API contract, schemas, SSE format

### Secondary (MEDIUM confidence)
- [Medium: Complete Guide to React + TypeScript + Vite 2026](https://medium.com/@robinviktorsson/complete-guide-to-setting-up-react-with-typescript-and-vite-2025-468f6556aaf2) - Project structure
- [GitHub: react-dropzone](https://github.com/react-dropzone/react-dropzone) - Fallback library if native DnD insufficient
- [DEV.to: Implementing Drag & Drop Without Libraries](https://dev.to/hexshift/implementing-drag-drop-file-uploads-in-react-without-external-libraries-1d31) - Native DnD patterns
- [Medium: Traefik localhost](https://medium.com/nerd-for-tech/how-to-use-traefik-on-localhost-2b566825f94f) - Local development routing

### Tertiary (LOW confidence)
- Community articles on SSE hooks - patterns verified against native EventSource API
- Various React TypeScript guides - patterns verified against official React docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Vite + React + TypeScript is well-documented, Iyeska standard
- Architecture: HIGH - Patterns verified against official docs and backend API
- Pitfalls: HIGH - Based on official documentation and common error patterns
- Traefik config: MEDIUM - General pattern known, exact implementation may vary

**Research date:** 2026-01-22
**Valid until:** 2026-04-22 (90 days - stable ecosystem, Vite 7.x is mature)
