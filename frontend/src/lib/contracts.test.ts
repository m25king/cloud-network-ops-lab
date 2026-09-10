import { describe, expect, it, vi, afterEach } from 'vitest';
import { reportSchema, statusSchema } from './contracts';
import { ApiError, getJson, retryRequest } from './api';
import { csvCell, toCsv } from './csv';
import report from '../../public/samples/probe-report.json';
afterEach(() => vi.unstubAllGlobals());
describe('report contract', () => {
  it('accepts real probe evidence', () => expect(reportSchema.safeParse(report).success).toBe(true));
  it('rejects fabricated success counts', () => { const r = structuredClone(report); r.results[0].successes = 0; expect(reportSchema.safeParse(r).success).toBe(false); });
  it('rejects misleading status', () => { const r = structuredClone(report); r.results[1].state = 'OK'; expect(reportSchema.safeParse(r).success).toBe(false); });
  it('rejects misleading failure ratio', () => { const r = structuredClone(report); r.results[0].request_failure_ratio = 1; expect(reportSchema.safeParse(r).success).toBe(false); });
  it('rejects invalid dates', () => expect(reportSchema.safeParse({...report, generated_at_utc:'yesterday'}).success).toBe(false));
});
describe('API boundary', () => {
  it('rejects HTTP 503 without displaying cached success', async () => { vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', {status:503}))); await expect(getJson('/api/status',statusSchema)).rejects.toMatchObject({status:503}); });
  it('rejects a successful response with invalid shape', async () => { vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}'))); await expect(getJson('/api/status',statusSchema)).rejects.toThrow('接口数据格式'); });
  it('does not retry client errors and bounds server retries', () => { expect(retryRequest(0,new ApiError('bad',400))).toBe(false); expect(retryRequest(0,new ApiError('down',503))).toBe(true); expect(retryRequest(1,new ApiError('down',503))).toBe(false); });
});
describe('CSV export', () => {
  it('neutralizes formula injection', () => expect(csvCell('  =SUM(A1)')).toBe("'  =SUM(A1)));
  it('escapes embedded quotes and preserves Chinese', () => expect(toCsv([['名称','a"b']])).toBe('\uFEFF"名称","a""b"'));
});

