import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

import { ProgressIndicator, ValidationResult } from "../components";
import { documentsApi } from "../services/api";

interface Validation {
  field_name: string;
  passed: boolean;
  error_message: string | null;
}

interface ReportData {
  document_id: string;
  overall_status: "pass" | "fail";
  validations: Validation[];
  fix_instructions: string[];
}

// Field name mapping for display
const FIELD_NAME_MAP: Record<string, string> = {
  hs_code: "HS 编码",
  invoice_value: "发票金额",
  invoice_date: "发票日期",
  shipper_name: "发货人名称",
  shipper_address: "发货人地址",
  consignee_name: "收货人名称",
  consignee_address: "收货人地址",
  product_description: "产品描述",
  document_date: "单据日期",
  item_count: "品项数量",
  item_count_match: "品项数量匹配",
  invoice_number_match: "发票号匹配",
  shipper_consistency: "发货人一致性",
  consignee_consistency: "收货人一致性",
};

export default function ResultsPage() {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!documentId) return;

    const fetchReport = async () => {
      try {
        const data = await documentsApi.getReport(documentId);
        setReport(data);
      } catch (err: any) {
        console.error("Failed to fetch report:", err);
        setError("获取报告失败，请重试");
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [documentId]);

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto text-center py-12">
        <ProgressIndicator />
        <p className="mt-4 text-gray-600">正在分析文档...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-3xl mx-auto">
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          {error || "无法加载报告"}
        </div>
        <button
          onClick={() => navigate("/")}
          className="mt-4 btn-primary"
        >
          返回上传
        </button>
      </div>
    );
  }

  const passedCount = report.validations.filter((v) => v.passed).length;
  const totalCount = report.validations.length;

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-8">
        <div
          className={`inline-flex items-center px-6 py-3 rounded-full text-lg font-bold ${
            report.overall_status === "pass"
              ? "bg-green-100 text-green-800"
              : "bg-red-100 text-red-800"
          }`}
        >
          {report.overall_status === "pass" ? "✅ 通过" : "❌ 未通过"}
        </div>
        <p className="text-gray-600 mt-2">
          检查结果: {passedCount}/{totalCount} 项通过
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">详细检查</h3>
        <div className="space-y-3">
          {report.validations.map((validation, index) => (
            <ValidationResult
              key={index}
              fieldName={FIELD_NAME_MAP[validation.field_name] || validation.field_name}
              passed={validation.passed}
              errorMessage={validation.error_message || undefined}
            />
          ))}
        </div>
      </div>

      {report.fix_instructions.length > 0 && (
        <div className="bg-yellow-50 rounded-lg border border-yellow-200 p-6">
          <h3 className="text-lg font-bold text-yellow-900 mb-4">修复建议</h3>
          <ul className="space-y-2">
            {report.fix_instructions.map((instruction, index) => (
              <li key={index} className="text-yellow-800">
                {instruction}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex gap-4 mt-8">
        <button 
          onClick={() => navigate("/")}
          className="flex-1 btn-primary"
        >
          检查新文档
        </button>
        <button 
          onClick={() => navigate(`/report/${documentId}`)}
          className="flex-1 btn-secondary"
        >
          下载 PDF 报告
        </button>
      </div>
    </div>
  );
}
