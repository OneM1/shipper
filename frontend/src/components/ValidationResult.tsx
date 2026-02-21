import { CheckCircle, XCircle } from "lucide-react";

interface ValidationResultProps {
  fieldName: string;
  passed: boolean;
  errorMessage?: string;
}

export default function ValidationResult({
  fieldName,
  passed,
  errorMessage,
}: ValidationResultProps) {
  return (
    <div
      className={`flex items-start p-4 rounded-lg ${
        passed ? "bg-green-50" : "bg-red-50"
      }`}
    >
      {passed ? (
        <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 mr-3" />
      ) : (
        <XCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3" />
      )}
      <div>
        <p
          className={`font-medium ${
            passed ? "text-green-800" : "text-red-800"
          }`}
        >
          {fieldName}
        </p>
        {!passed && errorMessage && (
          <p className="text-red-600 text-sm mt-1">{errorMessage}</p>
        )}
      </div>
    </div>
  );
}
