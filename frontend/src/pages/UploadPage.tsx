import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { UploadZone } from "../components";
import { documentsApi } from "../services/api";

export default function UploadPage() {
  const navigate = useNavigate();
  const [invoiceFile, setInvoiceFile] = useState<File | null>(null);
  const [packingListFile, setPackingListFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!invoiceFile || !packingListFile) return;

    setIsUploading(true);
    setError(null);

    try {
      const response = await documentsApi.upload(invoiceFile, packingListFile);
      // Navigate to results page with the document ID
      navigate(`/results/${response.document_id}`);
    } catch (err: any) {
      console.error("Upload failed:", err);
      setError(err.message || "上传失败，请重试");
    } finally {
      setIsUploading(false);
    }
  };

  const canSubmit = invoiceFile && packingListFile && !isUploading;

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">上传单证</h2>
      <p className="text-gray-600 mb-8">
        请上传商业发票和装箱单，我们将在 30 秒内完成合规检查
      </p>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error}
        </div>
      )}

      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">
            1. 商业发票 (Commercial Invoice)
          </h3>
          {invoiceFile ? (
            <div className="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg p-4">
              <span className="text-green-800">{invoiceFile.name}</span>
              <button
                onClick={() => setInvoiceFile(null)}
                className="text-green-600 hover:text-green-800"
              >
                移除
              </button>
            </div>
          ) : (
            <UploadZone
              onFileSelect={setInvoiceFile}
              label="上传商业发票"
            />
          )}
        </div>

        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-3">
            2. 装箱单 (Packing List)
          </h3>
          {packingListFile ? (
            <div className="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg p-4">
              <span className="text-green-800">{packingListFile.name}</span>
              <button
                onClick={() => setPackingListFile(null)}
                className="text-green-600 hover:text-green-800"
              >
                移除
              </button>
            </div>
          ) : (
            <UploadZone
              onFileSelect={setPackingListFile}
              label="上传装箱单"
            />
          )}
        </div>

        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="w-full btn-primary py-3 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? "上传中..." : "开始检查"}
        </button>
      </div>

      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <h4 className="font-medium text-blue-900 mb-2">检查项目</h4>
        <ul className="text-blue-800 text-sm space-y-1">
          <li>• HS 编码完整性和格式</li>
          <li>• 发票金额和币种</li>
          <li>• 收发货人信息完整性</li>
          <li>• 产品描述清晰度</li>
          <li>• 发票与装箱单一致性</li>
          <li>• 必填日期字段</li>
        </ul>
      </div>
    </div>
  );
}
