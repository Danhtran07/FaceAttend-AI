interface EmptyStateProps {
  title?: string;
  message?: string;
}

export default function EmptyState({
  title = "No data found",
  message = "There are no records to display.",
}: EmptyStateProps) {
  return (
    <div className="flex min-h-[240px] items-center justify-center">
      <div className="text-center">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-xl text-slate-400">
          ∅
        </div>

        <h3 className="text-sm font-bold text-slate-700">
          {title}
        </h3>

        <p className="mt-1 text-sm text-slate-500">
          {message}
        </p>
      </div>
    </div>
  );
}