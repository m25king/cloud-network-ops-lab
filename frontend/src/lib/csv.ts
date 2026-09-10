/** Export displayed records only; neutralize spreadsheet formula prefixes. */
export function csvCell(value: unknown): string {
  let text = String(value ?? '');
  if (/^[\s]*[=+@-]|^[\t\r\n]/.test(text)) text = "'" + text;
  return '"' + text.replaceAll('"', '""') + '"';
}
export function toCsv(rows: unknown[][]): string { return '\uFEFF' + rows.map(row => row.map(csvCell).join(',')).join('\r\n'); }
export function downloadCsv(name: string, rows: unknown[][]) {
  const url = URL.createObjectURL(new Blob([toCsv(rows)], { type: 'text/csv;charset=utf-8;' }));
  const link = document.createElement('a'); link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
