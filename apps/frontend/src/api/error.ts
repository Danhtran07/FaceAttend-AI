import axios from "axios";

export function getApiErrorMessage(
  error: unknown,
  fallback = "An unexpected error occurred."
): string {
  // Không phải Axios error
  if (!axios.isAxiosError(error)) {
    if (error instanceof Error) {
      return error.message;
    }

    return fallback;
  }

  // Backend có response
  if (error.response) {
    const status = error.response.status;

    const detail =
      error.response.data?.detail;

    // FastAPI thường trả detail
    if (typeof detail === "string") {
      return detail;
    }

    switch (status) {
      case 400:
        return "Bad request.";

      case 401:
        return "Your session has expired. Please login again.";

      case 403:
        return "You do not have permission to perform this action.";

      case 404:
        return "The requested resource was not found.";

      case 409:
        return "This data already exists.";

      case 422:
        return "The submitted data is invalid.";

      case 500:
        return "Internal server error.";

      case 502:
        return "The server is currently unavailable.";

      case 503:
        return "The server is currently unavailable.";

      default:
        return `Request failed with status ${status}.`;
    }
  }

  // Request được gửi nhưng không nhận response
  if (error.request) {
    if (error.code === "ECONNABORTED") {
      return "The request timed out. Please try again.";
    }

    return (
      "Unable to connect to the server. " +
      "Please make sure the backend is running."
    );
  }

  return fallback;
}