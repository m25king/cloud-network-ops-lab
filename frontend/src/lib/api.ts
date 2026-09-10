import type { z } from 'zod';
export class ApiError extends Error {
  constructor(message: string, public status?: number) { super(message); this.name = 'ApiError'; }
}
export async function getJson<T>(path: string, schema: z.ZodType<T>, signal?: AbortSignal): Promise<T> {
  const timeout = AbortSignal.timeout(6000);
  let response: Response;
  try {
    response = await fetch(path, { signal: signal ? AbortSignal.any([signal, timeout]) : timeout, cache: 'no-store', headers: { Accept: 'application/json' } });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError('连接超时或网络不可达，请确认后端已启动。');
  }
  if (!response.ok) throw new ApiError(response.status === 503 ? '后端服务暂不可用，请检查数据库依赖。' : `请求失败（HTTP ${response.status}）。`, response.status);
  let raw: unknown;
  try { raw = await response.json(); } catch { throw new ApiError('接口未返回有效 JSON，请检查代理配置。'); }
  const parsed = schema.safeParse(raw);
  if (!parsed.success) throw new ApiError('接口数据格式与约定不一致，已停止展示该结果。');
  return parsed.data;
}
export function retryRequest(count: number, error: Error) {
  return count < 1 && (!(error instanceof ApiError) || error.status === undefined || error.status >= 500);
}
