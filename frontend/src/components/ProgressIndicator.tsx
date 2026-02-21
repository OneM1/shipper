interface ProgressIndicatorProps {
  status: "uploading" | "processing" | "completed" | "error";
  progress: number;
  message: string;
}

export default function ProgressIndicator({
  status,
  progress,
  message,
}: ProgressIndicatorProps) {
  const statusColors = {
    uploading: "bg-primary-600",
    processing: "bg-yellow-500",
    completed: "bg-green-500",
    error: "bg-red-500",
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="mb-2 flex justify-between text-sm">
        <span className="text-gray-700">{message}</span>
        <span className="text-gray-500">{progress}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className={`h-2.5 rounded-full transition-all duration-300 ${statusColors[status]}`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
