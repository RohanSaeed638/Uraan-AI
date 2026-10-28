import { api } from "./client";
import { CareerDocument, DocumentKind } from "@/types/api";

export interface GenerateDocumentInput {
  kind: DocumentKind;
  target_role: string;
  details?: string;
  job_description?: string;
}

export async function generateDocument(input: GenerateDocumentInput) {
  const { data } = await api.post<CareerDocument>("/documents/generate", {
    ...input,
    details: input.details || undefined,
    job_description: input.job_description || undefined,
  });
  return data;
}

export async function updateDocument(
  id: string,
  changes: { title?: string; content?: string }
) {
  const { data } = await api.patch<CareerDocument>(`/documents/${id}`, changes);
  return data;
}

export async function deleteDocument(id: string) {
  await api.delete(`/documents/${id}`);
}
