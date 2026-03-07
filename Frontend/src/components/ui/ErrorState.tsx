export function ErrorState({
  title = "Something went wrong",
  message,
  action
}: {
  title?: string;
  message: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-clay/20 bg-white/80 p-5 shadow-card">
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="mt-2 text-sm text-ink/70">{message}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
