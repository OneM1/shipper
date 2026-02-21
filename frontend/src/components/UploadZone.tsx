import { Upload } from "lucide-react";
import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

import { cn } from "../utils/cn";

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  label: string;
  accept?: Record<string, string[]>;
}

export default function UploadZone({
  onFileSelect,
  label,
  accept = {
    "application/pdf": [".pdf"],
    "image/*": [".png", ".jpg", ".jpeg"],
  },
}: UploadZoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    multiple: false,
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
        isDragActive
          ? "border-primary-500 bg-primary-50"
          : "border-gray-300 hover:border-gray-400"
      )}
    >
      <input {...getInputProps()} />
      <Upload className="w-10 h-10 mx-auto mb-3 text-gray-400" />
      <p className="text-gray-700 font-medium">{label}</p>
      <p className="text-gray-500 text-sm mt-1">
        拖放文件到此处，或点击选择文件
      </p>
      <p className="text-gray-400 text-xs mt-2">支持 PDF、PNG、JPG 格式</p>
    </div>
  );
}
