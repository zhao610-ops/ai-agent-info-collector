export function Notice({ message, error = false }: { message: string; error?: boolean }) {
  if (!message) return null;
  return <div className={`rounded-lg border px-4 py-3 text-sm ${error ? "border-red-200 bg-red-50 text-red-700" : "border-blue-200 bg-blue-50 text-blue-700"}`}>{message}</div>;
}
