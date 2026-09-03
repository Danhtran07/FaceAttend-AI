interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorState({
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex min-h-[240px] items-center justify-center">
      <div className="max-w-md rounded-xl border border-red-200 bg-red-50 p-6 text-center">
        <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-red-100 text-red-600">
          !
        </div>

        <h3 className="text-sm font-bold text-red-800">
          Something went wrong
        </h3>

        <p className="mt-2 text-sm text-red-600">
          {message}
        </p>

        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
          >
            Try Again
          </button>
        )}
      </div>
    </div>
  );
}