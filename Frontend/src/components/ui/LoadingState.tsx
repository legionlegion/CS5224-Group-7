export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-center">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-moss/20 border-t-moss" />
      <p className="text-sm text-ink/70">{label}</p>
    </div>
  );
}
