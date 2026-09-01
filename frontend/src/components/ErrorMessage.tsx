interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorMessage({
  message,
  onRetry,
}: ErrorMessageProps) {

  return (
    <div className="error-state">

      <div className="error-state-icon">
        ⚠
      </div>

      <h3>
        Something went wrong
      </h3>

      <p>
        {message}
      </p>

      {onRetry && (
        <button
          type="button"
          className="primary-button"
          onClick={onRetry}
        >
          Try Again
        </button>
      )}

    </div>
  );
}