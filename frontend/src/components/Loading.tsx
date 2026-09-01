interface LoadingProps {
  message?: string;
}

export default function Loading({
  message = "Loading...",
}: LoadingProps) {

  return (
    <div className="loading-state">

      <div className="loading-spinner" />

      <p>{message}</p>

    </div>
  );
}