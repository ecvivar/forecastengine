import { Inbox } from "lucide-react";

interface EmptyStateProps {
  title?: string;
  message?: string;
}

export function EmptyState({
  title = "No data available",
  message = "There is nothing to display yet.",
}: EmptyStateProps) {
  return (
    <div className="container-page flex flex-col items-center justify-center py-16 text-center">
      <Inbox className="w-12 h-12 text-gray-300 mb-4" />
      <h2 className="text-xl font-bold mb-2 text-gray-800">{title}</h2>
      <p className="text-gray-500 max-w-md">{message}</p>
    </div>
  );
}
