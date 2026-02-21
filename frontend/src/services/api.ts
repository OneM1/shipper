import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8001";

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000, // 30 seconds
});

// API endpoints
export const documentsApi = {
  upload: async (invoice: File, packingList: File) => {
    const formData = new FormData();
    formData.append("invoice", invoice);
    formData.append("packing_list", packingList);

    const response = await apiClient.post("/documents/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  getStatus: async (documentId: string) => {
    const response = await apiClient.get(`/documents/${documentId}/status`);
    return response.data;
  },

  getReport: async (documentId: string) => {
    const response = await apiClient.get(`/documents/${documentId}/report`);
    return response.data;
  },

  downloadPDF: async (documentId: string) => {
    const response = await apiClient.get(`/documents/${documentId}/report.pdf`, {
      responseType: "blob",
    });
    return response.data;
  },
};

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors
    if (error.response?.status === 413) {
      return Promise.reject(new Error("文件大小超过限制"));
    }
    if (error.response?.status === 415) {
      return Promise.reject(new Error("不支持的文件格式"));
    }
    return Promise.reject(error);
  }
);
