import { API_URL, apiDelete, apiGet } from "./api";

export type Document = {
  id: string;
  vault_item_id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  uploaded_at: string;
};

export type DocumentUploadResult = {
  document: Document;
  message: string;
};

export function listDocuments(vaultId: string, itemId: string): Promise<Document[]> {
  return apiGet<Document[]>(`/vaults/${vaultId}/items/${itemId}/documents`);
}

export async function uploadDocument(
  vaultId: string,
  itemId: string,
  file: File
): Promise<DocumentUploadResult> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_URL}/vaults/${vaultId}/items/${itemId}/documents`, {
    method: "POST",
    headers: { Authorization: `Bearer ${getAccessToken()}` },
    body: form,
  });

  if (!res.ok) {
    let message = "Upload failed";
    try {
      const body = (await res.json()) as { error?: { message?: string } };
      message = body.error?.message ?? message;
    } catch {
      // non-JSON error body
    }
    throw new Error(message);
  }

  return (await res.json()) as DocumentUploadResult;
}

export async function downloadDocument(
  vaultId: string,
  itemId: string,
  documentId: string
): Promise<void> {
  const res = await fetch(
    `${API_URL}/vaults/${vaultId}/items/${itemId}/documents/${documentId}/download`,
    {
      method: "GET",
      headers: { Authorization: `Bearer ${getAccessToken()}` },
    }
  );

  if (!res.ok) {
    let message = "Download failed";
    try {
      const body = (await res.json()) as { error?: { message?: string } };
      message = body.error?.message ?? message;
    } catch {
      // non-JSON error body
    }
    throw new Error(message);
  }

  const blob = await res.blob();
  const disposition = res.headers.get("content-disposition") ?? "";
  const match = /filename="?([^";]+)"?/.exec(disposition);
  const filename = match?.[1] ?? "document";

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function getAccessToken(): string {
  if (typeof window === "undefined") return "";
  return window.sessionStorage.getItem("lifelink_access_token") ?? "";
}

export function deleteDocument(vaultId: string, itemId: string, documentId: string): Promise<void> {
  return apiDelete(`/vaults/${vaultId}/items/${itemId}/documents/${documentId}`);
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
