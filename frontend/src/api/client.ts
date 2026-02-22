import type { ApiErrorBody } from "@/types/api";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

function formatErrorMessage(body: ApiErrorBody): string {
  if (Array.isArray(body.detail)) {
    return body.detail.map((d) => `${d.loc.join(".")}: ${d.msg}`).join("; ");
  }
  return body.detail ?? body.error;
}

export class ApiError extends Error {
  status: number
  body: ApiErrorBody

  constructor(status: number, body: ApiErrorBody) {
    super(formatErrorMessage(body));
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!res.ok) {
    let body: ApiErrorBody;
    try {
      body = (await res.json()) as ApiErrorBody;
    } catch {
      throw new ApiError(res.status, { error: res.statusText });
    }
    throw new ApiError(res.status, body);
  }

  return (await res.json()) as T;
}

export function get<T>(path: string): Promise<T> {
  return request<T>(path);
}

export function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: body != null ? JSON.stringify(body) : undefined,
  });
}

export function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: "DELETE" });
}
