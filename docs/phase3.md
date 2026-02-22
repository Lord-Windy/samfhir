# Phase 3: React Frontend

## Goal

Build a React/TypeScript SPA that provides a user-friendly interface for browsing
FHIR patient data and performing write operations against the backend API. Serve
the built frontend directly from FastAPI via `StaticFiles` for a
single-deployment-unit architecture.

### What Changes from Phase 2

Phase 2 delivered a fully working backend API against live HAPI FHIR. The
backend endpoints stay untouched. Phase 3 adds:

1. A new `frontend/` directory containing a Vite + React + TypeScript application
2. A typed API client layer mirroring all backend DTOs
3. Pages for patient search, patient dashboard, observation entry, and cache stats
4. Deployment integration: FastAPI serves the built React `dist/` via `StaticFiles`
5. Multi-stage Dockerfile changes to build frontend assets alongside the Python
   backend
6. Updated `docker-compose.yml` and `Makefile` for frontend dev workflow

No backend endpoint changes are needed — the React frontend consumes the Phase 2
API as-is.

---

## Prerequisites

- Phase 2 complete and deployed (all endpoints live against HAPI FHIR)
- CORS already configured: `settings.cors_origins` defaults to
  `["http://localhost:5173"]`
- Node.js 20+ and npm available for local development
- Backend API running on `http://localhost:8000` during development

---

## Implementation Plan

### Step 1: Frontend Project Scaffolding

Create the Vite + React + TypeScript project with Tailwind CSS and shadcn/ui.

**Files to create:**

| File | Purpose |
| ---- | ------- |
| `frontend/package.json` | Project metadata, scripts, dependencies |
| `frontend/tsconfig.json` | Root TypeScript config (references) |
| `frontend/tsconfig.app.json` | App-specific TS config (strict, JSX) |
| `frontend/tsconfig.node.json` | Node/Vite config TS settings |
| `frontend/vite.config.ts` | Vite config with API proxy to port 8000 |
| `frontend/index.html` | HTML entry point |
| `frontend/tailwind.config.ts` | Tailwind CSS configuration |
| `frontend/postcss.config.js` | PostCSS with Tailwind + autoprefixer |
| `frontend/components.json` | shadcn/ui configuration |
| `frontend/src/main.tsx` | React entry point |
| `frontend/src/App.tsx` | Root component (placeholder) |
| `frontend/src/index.css` | Tailwind directives + shadcn CSS variables |
| `frontend/src/lib/utils.ts` | `cn()` utility for Tailwind class merging |

**What it does:**

Scaffold with `npm create vite@latest frontend -- --template react-ts`, then add:
- `tailwindcss`, `@tailwindcss/vite` (or `postcss` + `autoprefixer`)
- `@tanstack/react-query` (v5)
- `react-router` (v7 — the package was renamed from `react-router-dom`)

Initialize shadcn/ui with `npx shadcn@latest init` and install base components:
`button`, `card`, `input`, `label`, `table`, `tabs`, `badge`, `alert`,
`separator`, `skeleton`, `sonner`

**Vite proxy configuration** (`vite.config.ts`):

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
```

The proxy lets the frontend dev server forward API calls to the backend, avoiding
CORS issues during development. The same origin-relative URLs (`/api/v1/...`)
work in production when FastAPI serves the static assets.

**Project structure:**

```
frontend/
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── components.json
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    ├── lib/
    │   └── utils.ts
    ├── api/
    │   ├── client.ts
    │   └── endpoints.ts
    ├── types/
    │   └── api.ts
    ├── hooks/
    │   ├── use-patients.ts
    │   ├── use-clinical.ts
    │   ├── use-mutations.ts
    │   ├── use-cache.ts
    │   └── use-health.ts
    ├── pages/
    │   ├── SearchPage.tsx
    │   ├── DashboardPage.tsx
    │   ├── ObservationFormPage.tsx
    │   └── CacheStatsPage.tsx
    ├── components/
    │   ├── ui/                  # shadcn/ui generated components
    │   ├── layout/
    │   │   ├── AppLayout.tsx
    │   │   ├── Header.tsx
    │   │   └── Nav.tsx
    │   ├── patient/
    │   │   ├── PatientCard.tsx
    │   │   ├── PatientSearchResults.tsx
    │   │   └── PatientDemographics.tsx
    │   ├── clinical/
    │   │   ├── ConditionsTable.tsx
    │   │   ├── ObservationsTable.tsx
    │   │   ├── MedicationsTable.tsx
    │   │   └── AllergiesTable.tsx
    │   ├── ConnectionStatus.tsx
    │   └── ErrorBoundary.tsx
    └── lib/
        └── utils.ts
```

### Step 2: TypeScript Types

Define TypeScript interfaces that mirror every backend Pydantic schema exactly.

**File to create:**

```
frontend/src/types/api.ts
```

**What it does:**

Mirrors the backend's `patient_schemas.py`, plus health/cache response shapes
and error response shapes. Dates are ISO strings (`"YYYY-MM-DD"`) since that's
what Pydantic serializes `date` fields to.

**Type definitions:**

```typescript
// Response types (mirror backend Pydantic schemas in patient_schemas.py)

export interface PatientResponse {
  id: string;
  family_name: string;
  given_name: string;
  birth_date: string;   // ISO date "YYYY-MM-DD"
  gender: string;
}

export interface ConditionResponse {
  id: string;
  code: string;
  display: string;
  clinical_status: string;
  onset_date: string | null;
}

export interface ObservationResponse {
  id: string;
  code: string;
  display: string;
  value: string;
  unit: string | null;
  effective_date: string | null;
}

export interface MedicationResponse {
  id: string;
  code: string;
  display: string;
  status: string;
  authored_on: string | null;
}

export interface AllergyResponse {
  id: string;
  code: string;
  display: string;
  clinical_status: string;
  criticality: string | null;
}

export interface PatientSummaryResponse {
  patient: PatientResponse;
  active_conditions: ConditionResponse[];
  recent_observations: ObservationResponse[];
  active_medications: MedicationResponse[];
  allergies: AllergyResponse[];
}

export interface CacheStatsResponse {
  hits: number;
  misses: number;
}

export interface HealthResponse {
  status: string;
  redis: string;
}

// Request types (mirror backend request schemas)

export interface CreateObservationRequest {
  patient_id: string;
  code: string;
  display: string;
  value: string;
  unit?: string | null;
  effective_date?: string | null;
}

export interface CreateConditionRequest {
  patient_id: string;
  code: string;
  display: string;
  clinical_status?: string;   // defaults to "active" on backend
  onset_date?: string | null;
}

// Error types

export interface ApiErrorBody {
  error: string;
  detail?: string;
  patient_id?: string;
}

export interface ValidationErrorBody {
  detail: Array<{
    loc: (string | number)[];
    msg: string;
    type: string;
  }>;
}
```

### Step 3: API Client Layer

Build a typed fetch wrapper with structured error handling and base URL
configuration.

**Files to create:**

| File | Purpose |
| ---- | ------- |
| `frontend/src/api/client.ts` | Base `fetchApi()` wrapper with error handling |
| `frontend/src/api/endpoints.ts` | One typed function per backend endpoint |

**`client.ts` — base fetch wrapper:**

```typescript
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: { error: string; detail?: string; patient_id?: string },
  ) {
    super(body.detail ?? body.error);
    this.name = 'ApiError';
  }
}

export async function fetchApi<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({
      error: 'unknown_error',
      detail: response.statusText,
    }));
    throw new ApiError(response.status, body);
  }

  return response.json() as Promise<T>;
}
```

`BASE_URL` defaults to empty string (same origin), which works for both dev
(Vite proxy) and production (FastAPI serves everything). Override via
`VITE_API_BASE_URL` env var if needed.

**`endpoints.ts` — typed endpoint functions:**

```typescript
// Read endpoints
export const searchPatients = (name?: string) =>
  fetchApi<PatientResponse[]>(
    `/api/v1/patients${name ? `?name=${encodeURIComponent(name)}` : ''}`
  );

export const getPatient = (id: string) =>
  fetchApi<PatientResponse>(`/api/v1/patients/${id}`);

export const getPatientSummary = (id: string) =>
  fetchApi<PatientSummaryResponse>(`/api/v1/patients/${id}/summary`);

export const getConditions = (patientId: string) =>
  fetchApi<ConditionResponse[]>(`/api/v1/patients/${patientId}/conditions`);

export const getObservations = (patientId: string) =>
  fetchApi<ObservationResponse[]>(`/api/v1/patients/${patientId}/observations`);

export const getMedications = (patientId: string) =>
  fetchApi<MedicationResponse[]>(`/api/v1/patients/${patientId}/medications`);

export const getAllergies = (patientId: string) =>
  fetchApi<AllergyResponse[]>(`/api/v1/patients/${patientId}/allergies`);

// Write endpoints
export const createObservation = (data: CreateObservationRequest) =>
  fetchApi<ObservationResponse>('/api/v1/observations', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const createCondition = (data: CreateConditionRequest) =>
  fetchApi<ConditionResponse>('/api/v1/conditions', {
    method: 'POST',
    body: JSON.stringify(data),
  });

// Cache endpoints
export const getCacheStats = () =>
  fetchApi<CacheStatsResponse>('/api/v1/cache/stats');

export const flushCache = () =>
  fetchApi<{ status: string }>('/api/v1/cache', { method: 'DELETE' });

// Health endpoints
export const getHealth = () => fetchApi<HealthResponse>('/health');
```

### Step 4: TanStack Query Setup and Custom Hooks

Configure the QueryClient and create custom hooks wrapping every API call.

**Files to create:**

| File | Purpose |
| ---- | ------- |
| `frontend/src/hooks/use-patients.ts` | `useSearchPatients`, `usePatient`, `usePatientSummary` |
| `frontend/src/hooks/use-clinical.ts` | `useConditions`, `useObservations`, `useMedications`, `useAllergies` |
| `frontend/src/hooks/use-mutations.ts` | `useCreateObservation`, `useCreateCondition` |
| `frontend/src/hooks/use-cache.ts` | `useCacheStats`, `useFlushCache` |
| `frontend/src/hooks/use-health.ts` | `useHealthCheck` |

**QueryClient configuration** (in `App.tsx`):

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,        // 30s before refetch
      retry: 1,                 // Retry once on failure
      refetchOnWindowFocus: false,
    },
  },
});
```

**Query key conventions:**

Structured keys for consistent invalidation:
- `['patients', 'search', name]`
- `['patients', id]`
- `['patients', id, 'summary']`
- `['patients', id, 'conditions']` / `'observations'` / `'medications'` /
  `'allergies'`
- `['cache', 'stats']`
- `['health']`

**Example — `use-patients.ts`:**

```typescript
export function useSearchPatients(name: string | undefined) {
  return useQuery({
    queryKey: ['patients', 'search', name],
    queryFn: () => searchPatients(name),
    enabled: name !== undefined && name.length >= 2,
  });
}

export function usePatient(id: string) {
  return useQuery({
    queryKey: ['patients', id],
    queryFn: () => getPatient(id),
  });
}

export function usePatientSummary(id: string | undefined) {
  return useQuery({
    queryKey: ['patients', id, 'summary'],
    queryFn: () => getPatientSummary(id!),
    enabled: !!id,
  });
}
```

**Example — `use-mutations.ts`:**

```typescript
export function useCreateObservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createObservation,
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['patients', variables.patient_id],
      });
    },
  });
}
```

**`use-health.ts` — polling health check:**

```typescript
export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 30_000,  // Poll every 30s
    retry: false,             // Don't retry — just show disconnected
  });
}
```

### Step 5: Routing

Set up React Router v7 with all application routes.

**File to modify:**

```
frontend/src/App.tsx
```

**Routes:**

| Path | Page Component | Description |
| ---- | -------------- | ----------- |
| `/` | `SearchPage` | Patient search / ID entry (home) |
| `/patients/:id` | `DashboardPage` | Patient dashboard with clinical data |
| `/patients/:id/observations/new` | `ObservationFormPage` | New observation entry form |
| `/cache` | `CacheStatsPage` | Cache statistics display |

**`App.tsx` structure:**

```typescript
import { BrowserRouter, Routes, Route } from 'react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppLayout } from './components/layout/AppLayout';
import { SearchPage } from './pages/SearchPage';
import { DashboardPage } from './pages/DashboardPage';
import { ObservationFormPage } from './pages/ObservationFormPage';
import { CacheStatsPage } from './pages/CacheStatsPage';

const queryClient = new QueryClient({ /* ... */ });

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<SearchPage />} />
            <Route path="patients/:id" element={<DashboardPage />} />
            <Route path="patients/:id/observations/new"
                   element={<ObservationFormPage />} />
            <Route path="cache" element={<CacheStatsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

`<AppLayout />` uses `<Outlet />` to render nested route content, providing a
consistent header/nav wrapper.

### Step 6: Layout and Shared Components

Build the application shell and reusable components.

**Files to create:**

| File | Purpose |
| ---- | ------- |
| `frontend/src/components/layout/AppLayout.tsx` | Page shell with header, nav, `<Outlet />` |
| `frontend/src/components/layout/Header.tsx` | App title + `ConnectionStatus` in top bar |
| `frontend/src/components/layout/Nav.tsx` | Navigation links (Search, Cache Stats) |
| `frontend/src/components/ConnectionStatus.tsx` | Green/amber/red dot based on `/health` |
| `frontend/src/components/ErrorBoundary.tsx` | Catch-all rendering error boundary |

**`AppLayout.tsx`:**

```typescript
export function AppLayout() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="container mx-auto flex gap-6 py-6">
        <Nav />
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
```

**`ConnectionStatus.tsx`:**

Polls `/health` every 30s via `useHealthCheck`. Three states:
- Green dot + "Connected" when `status === "ok"` and `redis === "connected"`
- Amber dot + "Degraded" when `status === "ok"` but `redis !== "connected"`
- Red dot + "Offline" when the health check fails

```typescript
export function ConnectionStatus() {
  const { data, isError } = useHealthCheck();

  const status = isError ? 'offline'
    : data?.redis === 'connected' ? 'connected'
    : 'degraded';

  const colors = {
    connected: 'bg-green-500',
    degraded: 'bg-amber-500',
    offline: 'bg-red-500',
  };

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className={`h-2 w-2 rounded-full ${colors[status]}`} />
      <span className="capitalize">{status}</span>
    </div>
  );
}
```

**`Nav.tsx`:**

Vertical nav with `NavLink` from React Router for active state styling:
- Search Patients (`/`)
- Cache Stats (`/cache`)

### Step 7: Patient Search Page

The home page — search by name or enter a patient ID directly.

**Files to create:**

| File | Purpose |
| ---- | ------- |
| `frontend/src/pages/SearchPage.tsx` | Search page with two modes |
| `frontend/src/components/patient/PatientSearchResults.tsx` | Renders search result list |
| `frontend/src/components/patient/PatientCard.tsx` | Single patient card (clickable → dashboard) |

**`SearchPage.tsx` design:**

Two sections:

1. **Search by name**: Text input with debounced search (300ms). Calls
   `useSearchPatients(debouncedName)`. Results rendered as clickable
   `PatientCard` components that navigate to `/patients/:id`.
2. **Go to patient by ID**: Text input + "View" button. Navigates to
   `/patients/:id` on submit.

```typescript
export function SearchPage() {
  const [searchName, setSearchName] = useState('');
  const [directId, setDirectId] = useState('');
  const debouncedName = useDebounce(searchName, 300);
  const navigate = useNavigate();

  const { data: patients, isLoading, isError, error } = useSearchPatients(
    debouncedName.length >= 2 ? debouncedName : undefined
  );

  const handleDirectLookup = (e: FormEvent) => {
    e.preventDefault();
    if (directId.trim()) navigate(`/patients/${directId.trim()}`);
  };

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader><CardTitle>Search Patients</CardTitle></CardHeader>
        <CardContent>
          <Input
            placeholder="Search by name (e.g., Smith)..."
            value={searchName}
            onChange={(e) => setSearchName(e.target.value)}
          />
          {isLoading && <Skeleton />}
          {patients && <PatientSearchResults patients={patients} />}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Look Up by Patient ID</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleDirectLookup} className="flex gap-2">
            <Input placeholder="Patient ID" value={directId} ... />
            <Button type="submit">View</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

**Debounce**: Implement a small `useDebounce` hook (~10 lines with
`useState`/`useEffect`/`setTimeout`). No external library needed.

**`PatientCard.tsx`:**

Clickable card showing `given_name family_name`, gender, birth date. Links to
`/patients/:id`.

### Step 8: Patient Dashboard Page

The core data display page. Shows demographics and all clinical data in tabs.

**Files to create:**

| File | Purpose |
| ---- | ------- |
| `frontend/src/pages/DashboardPage.tsx` | Dashboard orchestrator |
| `frontend/src/components/patient/PatientDemographics.tsx` | Demographics card |
| `frontend/src/components/clinical/ConditionsTable.tsx` | Conditions table |
| `frontend/src/components/clinical/ObservationsTable.tsx` | Observations table |
| `frontend/src/components/clinical/MedicationsTable.tsx` | Medications table |
| `frontend/src/components/clinical/AllergiesTable.tsx` | Allergies table |

**`DashboardPage.tsx` design:**

Uses `useParams()` to get the patient ID. Calls `usePatientSummary(id)` to
fetch all data in one request. Displays:

1. **Demographics** at top (name, DOB, gender, ID)
2. **Action button**: "Add Observation" → `/patients/:id/observations/new`
3. **Tabbed clinical data** via shadcn `Tabs`:
   - Conditions (default)
   - Observations
   - Medications
   - Allergies

```typescript
export function DashboardPage() {
  const { id } = useParams<{ id: string }>();
  const { data: summary, isLoading, isError, error } = usePatientSummary(id);

  if (isLoading) return <DashboardSkeleton />;
  if (isError) return <ErrorDisplay error={error} />;
  if (!summary) return null;

  return (
    <div className="space-y-6">
      <PatientDemographics patient={summary.patient} />

      <div className="flex justify-end">
        <Button asChild>
          <Link to={`/patients/${id}/observations/new`}>
            Add Observation
          </Link>
        </Button>
      </div>

      <Tabs defaultValue="conditions">
        <TabsList>
          <TabsTrigger value="conditions">
            Conditions ({summary.active_conditions.length})
          </TabsTrigger>
          <TabsTrigger value="observations">
            Observations ({summary.recent_observations.length})
          </TabsTrigger>
          <TabsTrigger value="medications">
            Medications ({summary.active_medications.length})
          </TabsTrigger>
          <TabsTrigger value="allergies">
            Allergies ({summary.allergies.length})
          </TabsTrigger>
        </TabsList>
        <TabsContent value="conditions">
          <ConditionsTable conditions={summary.active_conditions} />
        </TabsContent>
        {/* ... other tabs ... */}
      </Tabs>
    </div>
  );
}
```

**Clinical table components:**

Each receives its typed array prop and renders a shadcn `Table`:

- **ConditionsTable**: Code, Display, Clinical Status, Onset Date
- **ObservationsTable**: Code, Display, Value, Unit, Effective Date
- **MedicationsTable**: Code, Display, Status, Authored On
- **AllergiesTable**: Code, Display, Clinical Status, Criticality

Use `Badge` for status fields (green for "active", red for "high" criticality).
Show "No data" when the array is empty.

**Error handling:**

- 404 (`patient_not_found`) → "Patient not found" message with link back to
  search
- 502/503 (FHIR server) → "FHIR server is currently unavailable" message

### Step 9: Observation Entry Form

A form for creating a new observation for a specific patient.

**File to create:**

```
frontend/src/pages/ObservationFormPage.tsx
```

**Design:**

Route: `/patients/:id/observations/new`. Patient ID pre-filled from URL.

Form fields (matching `CreateObservationRequest`):
- **Patient ID** (read-only, from URL)
- **Code** (text input, required — e.g., `"8480-6"`)
- **Display** (text input, required — e.g., `"Systolic Blood Pressure"`)
- **Value** (text input, required — e.g., `"120"`)
- **Unit** (text input, optional — e.g., `"mmHg"`)
- **Effective Date** (date input, optional — defaults to today)

**Quick-select presets** for common observations:

| Preset | Code | Display | Unit |
| ------ | ---- | ------- | ---- |
| BP Systolic | `8480-6` | Systolic Blood Pressure | mmHg |
| BP Diastolic | `8462-4` | Diastolic Blood Pressure | mmHg |
| Heart Rate | `8867-4` | Heart Rate | bpm |
| Body Temperature | `8310-5` | Body Temperature | degC |

Clicking a preset populates code, display, and unit — user only enters the
value.

**Submission flow:**

1. Client-side validation (required fields)
2. Call `useCreateObservation().mutateAsync(data)`
3. On success: show success toast (via `sonner`), navigate to `/patients/:id`
4. On error: show error message inline

```typescript
export function ObservationFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const mutation = useCreateObservation();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    await mutation.mutateAsync({
      patient_id: id!,
      code: formData.get('code') as string,
      display: formData.get('display') as string,
      value: formData.get('value') as string,
      unit: (formData.get('unit') as string) || undefined,
      effective_date: (formData.get('effective_date') as string) || undefined,
    });
    navigate(`/patients/${id}`);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>New Observation</CardTitle>
        <CardDescription>Patient ID: {id}</CardDescription>
      </CardHeader>
      <CardContent>
        {/* Preset buttons */}
        {/* Form fields */}
        {/* Submit button with loading state */}
      </CardContent>
    </Card>
  );
}
```

### Step 10: Cache Stats Page

Display cache hit/miss statistics.

**File to create:**

```
frontend/src/pages/CacheStatsPage.tsx
```

**Design:**

- Calls `useCacheStats()` with `refetchInterval: 10_000` (auto-refresh every
  10s)
- Shows: hit count, miss count, hit rate percentage
- "Flush Cache" button calls `useFlushCache` mutation, then invalidates the
  stats query

```typescript
export function CacheStatsPage() {
  const { data: stats } = useCacheStats();
  const flushMutation = useFlushCache();

  const total = (stats?.hits ?? 0) + (stats?.misses ?? 0);
  const hitRate = total > 0
    ? ((stats!.hits / total) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Cache Statistics</h1>
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Hits" value={stats?.hits ?? 0} />
        <StatCard label="Misses" value={stats?.misses ?? 0} />
        <StatCard label="Hit Rate" value={`${hitRate}%`} />
      </div>
      <Button
        variant="destructive"
        onClick={() => flushMutation.mutate()}
        disabled={flushMutation.isPending}
      >
        Flush Cache
      </Button>
    </div>
  );
}
```

### Step 11: Connection Status Indicator

Wire the health check indicator into the application header.

**Implementation details:**

- Rendered in `Header.tsx` at the far right
- Uses `useHealthCheck()` which polls `/health` every 30s
- Three states: connected (green), degraded (amber), offline (red)
- On first load, shows a pulsing gray dot until the first check completes
- Does not block page rendering — the health check runs asynchronously

Already described in Step 6. This step is about integration and edge cases.

### Step 12: Deployment Integration

Wire the built React frontend into FastAPI for single-origin serving.

**Files to modify:**

| File | Change |
| ---- | ------ |
| `backend/src/samfhir/main.py` | Add `StaticFiles` mount for frontend dist |
| `backend/Dockerfile` | Add Node.js build stage, copy dist into Python image |
| `docker-compose.yml` | Update build context to project root |

**`main.py` changes:**

Add a `StaticFiles` mount **after** all API routers. The `html=True` parameter
enables SPA fallback routing (serves `index.html` when no API route matches).
Guarded by `static_dir.is_dir()` so it's skipped during dev and testing.

```python
from pathlib import Path
from fastapi.staticfiles import StaticFiles

def create_app() -> FastAPI:
    # ... existing setup ...

    # existing router includes ...
    application.include_router(seed_router)

    # Serve frontend static assets (production only)
    static_dir = Path(__file__).parent / "static"
    if static_dir.is_dir():
        application.mount(
            "/", StaticFiles(directory=static_dir, html=True), name="static"
        )

    return application
```

**Dockerfile changes** (`backend/Dockerfile`):

Add a Node.js build stage before the Python build. The Dockerfile context
changes from `backend/` to the project root.

```dockerfile
# Stage 1: Build React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Build Python backend (existing, adjusted paths)
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --no-dev --no-install-project
COPY backend/src/ src/
# Copy frontend build output into the backend's static directory
COPY --from=frontend-builder /frontend/dist src/samfhir/static/
RUN uv sync --no-dev

# Stage 3: Runtime (unchanged)
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["uvicorn", "samfhir.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`docker-compose.yml` changes:**

Update the API service build context from `backend/` to `.` with an explicit
`dockerfile`:

```yaml
services:
  api:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      SAMFHIR_REDIS_URL: redis://redis:6379/0
    depends_on:
      redis:
        condition: service_started

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

**Dev workflow recommendation:** Run `docker compose up` for backend + Redis,
then `cd frontend && npm run dev` separately. The Vite proxy handles API
forwarding. No Docker service needed for the frontend during development.

### Step 13: Testing Strategy

**Frontend testing approach:**

| Layer | Tool | What's Tested |
| ----- | ---- | ------------- |
| Unit (components) | Vitest + React Testing Library | Component rendering, user interactions |
| Unit (hooks) | Vitest + React Testing Library | Hook behavior with mocked fetch |
| Unit (API client) | Vitest | `fetchApi` error handling, URL construction |

**Files to create:**

| File | Purpose |
| ---- | ------- |
| `frontend/src/test-setup.ts` | Test setup (imports `@testing-library/jest-dom`) |
| `frontend/src/api/__tests__/client.test.ts` | Test fetchApi error handling |
| `frontend/src/api/__tests__/endpoints.test.ts` | Test URL construction and request bodies |
| `frontend/src/hooks/__tests__/use-patients.test.ts` | Test query hooks with mocked API |
| `frontend/src/pages/__tests__/SearchPage.test.tsx` | Test search interaction flow |
| `frontend/src/pages/__tests__/DashboardPage.test.tsx` | Test dashboard rendering |
| `frontend/src/components/__tests__/ConnectionStatus.test.tsx` | Test indicator states |

**Dev dependencies to add:**

```json
{
  "devDependencies": {
    "vitest": "...",
    "@testing-library/react": "...",
    "@testing-library/jest-dom": "...",
    "@testing-library/user-event": "...",
    "msw": "..."
  }
}
```

Use MSW (Mock Service Worker) for mocking `fetch` calls in tests — tests the
full hook-to-fetch chain without mocking the API client directly.

**Vitest configuration** (in `vite.config.ts`):

```typescript
export default defineConfig({
  // ... existing config ...
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
  },
})
```

### Step 14: Makefile and Workflow Updates

Update the `Makefile` to support frontend development commands.

**File to modify:**

```
Makefile
```

**New/modified targets:**

```makefile
.PHONY: dev test lint format build deploy \
        frontend-dev frontend-build frontend-lint frontend-test \
        test-all lint-all

# Backend
dev:
	docker compose up --build

test:
	cd backend && uv run pytest

lint:
	cd backend && uv run ruff check .

format:
	cd backend && uv run ruff format .

# Frontend
frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-lint:
	cd frontend && npm run lint

frontend-test:
	cd frontend && npm run test

# Combined
test-all: test frontend-test

lint-all: lint frontend-lint

# Build (production image with frontend)
build:
	docker build -t samfhir-api -f backend/Dockerfile .

deploy: build
	docker tag samfhir-api australia-southeast1-docker.pkg.dev/samfhir/samfhir/api:latest
	docker push australia-southeast1-docker.pkg.dev/samfhir/samfhir/api:latest
	gcloud run deploy samfhir-api \
		--image australia-southeast1-docker.pkg.dev/samfhir/samfhir/api:latest \
		--region australia-southeast1 \
		--platform managed
```

Note: `build` changes from `docker build -t samfhir-api backend/` to
`docker build -t samfhir-api -f backend/Dockerfile .` since the build context
is now the project root.

**`.gitignore` additions:**

```
frontend/node_modules/
frontend/dist/
```

---

## Acceptance Criteria

- [ ] Frontend loads at the configured URL (localhost:5173 in dev, same origin
      in prod)
- [ ] User can search for patients by name and see results
- [ ] User can enter a patient ID directly and navigate to their dashboard
- [ ] Patient dashboard displays real demographics, conditions, observations,
      medications, allergies from HAPI FHIR
- [ ] User can submit a new observation via the form and see it reflected on
      the dashboard
- [ ] Cache stats are visible in the UI with hit count, miss count, and hit rate
- [ ] Connection status indicator shows green when healthy, red when API is
      unreachable
- [ ] 404 errors (unknown patient) display a user-friendly message
- [ ] 502/503 errors (FHIR server down) display a user-friendly message
- [ ] `make build` produces a Docker image that serves both API and frontend
- [ ] Works in Chrome and Firefox
- [ ] `make frontend-test` passes
- [ ] `make frontend-lint` passes

---

## Key Decisions

| Decision            | Choice               | Rationale                                                     |
| ------------------- | -------------------- | ------------------------------------------------------------- |
| Build tool          | Vite                 | Fast HMR, native TypeScript, modern ESM-first.                |
| Component library   | shadcn/ui + Tailwind | Copy-paste components, no runtime dependency. Accessible.     |
| State management    | TanStack Query v5    | Handles caching, loading/error states, refetching, mutations. |
| Routing             | React Router v7      | Standard SPA routing. Only 4 routes needed.                   |
| HTTP client         | Native `fetch`       | No extra dependency. Typed wrapper provides safety.           |
| Serving (prod)      | FastAPI `StaticFiles` | Single deployment unit on Cloud Run. Simple.                  |
| Serving (dev)       | Vite dev server + proxy | Vite proxies `/api` and `/health` to FastAPI on port 8000. |
| Testing             | Vitest + RTL + MSW   | Same Vite toolchain. MSW mocks fetch at the network level.    |

---

## Implementation Order

```
Step 1: Frontend project scaffolding (Vite + React + TS + Tailwind + shadcn)
  │
  ├── Step 2: TypeScript types (parallel with Step 1)
  │
  ▼
Step 3: API client layer (depends on types)
  │
  ▼
Step 4: TanStack Query hooks (depends on API client)
  │
  ├── Step 5: Routing (parallel with Step 6)
  │
  ▼
Step 6: Layout + shared components (depends on hooks)
  │
  ├─── Steps 7, 8, 9, 10 are independent of each other ───┤
  │                                                          │
  ▼                                                          ▼
Step 7: Search page              Step 8: Dashboard page
Step 9: Observation form         Step 10: Cache stats page
  │                                                          │
  ├────────────────────── merge ─────────────────────────────┤
  │
  ▼
Step 11: Connection status (polish, depends on layout)
  │
  ▼
Step 12: Deployment integration (StaticFiles, Dockerfile, docker-compose)
  │
  ▼
Step 13: Tests
  │
  ▼
Step 14: Makefile + .gitignore updates
  │
  ▼
Deploy + verify acceptance criteria
```

**Parallelizable work:**

- Steps 1 and 2 are independent
- Steps 7, 8, 9, and 10 (pages) are independent of each other once Steps 4–6
  are complete
- Step 13 (tests) can be written alongside each page step but is listed at the
  end for clarity
- Step 14 (Makefile) can be done at any point after Step 1

---

## Files Summary

**New files:**

| File | Purpose |
| ---- | ------- |
| `frontend/package.json` | Project metadata, scripts, dependencies |
| `frontend/tsconfig.json` | Root TypeScript config |
| `frontend/tsconfig.app.json` | App TS config |
| `frontend/tsconfig.node.json` | Node TS config |
| `frontend/vite.config.ts` | Vite config with proxy and test setup |
| `frontend/tailwind.config.ts` | Tailwind configuration |
| `frontend/postcss.config.js` | PostCSS config |
| `frontend/components.json` | shadcn/ui config |
| `frontend/index.html` | HTML entry point |
| `frontend/src/main.tsx` | React entry point |
| `frontend/src/App.tsx` | Root component with routing and QueryClient |
| `frontend/src/index.css` | Tailwind directives + shadcn CSS variables |
| `frontend/src/lib/utils.ts` | `cn()` utility |
| `frontend/src/types/api.ts` | TypeScript interfaces mirroring backend DTOs |
| `frontend/src/api/client.ts` | Base fetch wrapper with error handling |
| `frontend/src/api/endpoints.ts` | Typed functions for each backend endpoint |
| `frontend/src/hooks/use-patients.ts` | Patient query hooks |
| `frontend/src/hooks/use-clinical.ts` | Clinical data query hooks |
| `frontend/src/hooks/use-mutations.ts` | Mutation hooks for writes |
| `frontend/src/hooks/use-cache.ts` | Cache stats hooks |
| `frontend/src/hooks/use-health.ts` | Health check polling hook |
| `frontend/src/pages/SearchPage.tsx` | Patient search page |
| `frontend/src/pages/DashboardPage.tsx` | Patient dashboard page |
| `frontend/src/pages/ObservationFormPage.tsx` | New observation form |
| `frontend/src/pages/CacheStatsPage.tsx` | Cache statistics page |
| `frontend/src/components/layout/AppLayout.tsx` | Application shell |
| `frontend/src/components/layout/Header.tsx` | Header with title + status |
| `frontend/src/components/layout/Nav.tsx` | Navigation links |
| `frontend/src/components/patient/PatientCard.tsx` | Patient summary card |
| `frontend/src/components/patient/PatientSearchResults.tsx` | Search results list |
| `frontend/src/components/patient/PatientDemographics.tsx` | Demographics display |
| `frontend/src/components/clinical/ConditionsTable.tsx` | Conditions table |
| `frontend/src/components/clinical/ObservationsTable.tsx` | Observations table |
| `frontend/src/components/clinical/MedicationsTable.tsx` | Medications table |
| `frontend/src/components/clinical/AllergiesTable.tsx` | Allergies table |
| `frontend/src/components/ConnectionStatus.tsx` | Health check indicator |
| `frontend/src/components/ErrorBoundary.tsx` | Error boundary |
| `frontend/src/components/ui/*` | shadcn/ui components (generated) |
| `frontend/src/test-setup.ts` | Test setup file |
| `frontend/src/api/__tests__/client.test.ts` | API client tests |
| `frontend/src/hooks/__tests__/use-patients.test.ts` | Hook tests |
| `frontend/src/pages/__tests__/SearchPage.test.tsx` | Search page tests |
| `frontend/src/pages/__tests__/DashboardPage.test.tsx` | Dashboard tests |

**Modified files:**

| File | Change |
| ---- | ------ |
| `backend/src/samfhir/main.py` | Add `StaticFiles` mount after all routers |
| `backend/Dockerfile` | Add Node.js build stage, copy frontend dist, adjust paths for root context |
| `docker-compose.yml` | Update build context from `backend/` to `.` |
| `Makefile` | Add frontend targets, update `build` context, add `test-all`/`lint-all` |
| `.gitignore` | Add `frontend/node_modules/`, `frontend/dist/` |
