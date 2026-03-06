export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="flex flex-col items-center gap-4">
        <div
          className="h-10 w-10 animate-spin rounded-full border-4 border-purple-200 border-t-purple-600"
          aria-label="Yükleniyor"
        />
        <p className="text-sm text-slate-500">Yükleniyor...</p>
      </div>
    </div>
  );
}
