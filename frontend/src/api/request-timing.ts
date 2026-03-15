type RequestId = symbol;

interface PendingRequest {
  path: string;
  startTime: number;
}

const SLOW_THRESHOLD_MS = 1000;

let pendingRequests = new Map<RequestId, PendingRequest>();
let listeners = new Set<() => void>();

export function startRequest(path: string): RequestId {
  const id = Symbol();
  pendingRequests.set(id, {
    path,
    startTime: Date.now(),
  });
  notifyListeners();
  return id;
}

export function endRequest(id: RequestId): void {
  pendingRequests.delete(id);
  notifyListeners();
}

export function getSlowRequestElapsed(): number | null {
  const now = Date.now();
  let maxElapsed = 0;

  for (const request of pendingRequests.values()) {
    const elapsed = now - request.startTime;
    if (elapsed >= SLOW_THRESHOLD_MS && elapsed > maxElapsed) {
      maxElapsed = elapsed;
    }
  }

  return maxElapsed > 0 ? maxElapsed : null;
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function notifyListeners(): void {
  for (const listener of listeners) {
    listener();
  }
}

export function reset(): void {
  pendingRequests = new Map();
  listeners = new Set();
}
