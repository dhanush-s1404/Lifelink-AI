import { apiGet, apiPost } from "./api";

export type EmergencyStatus = "pending" | "escalated" | "resolved" | "cancelled";

export type Emergency = {
  id: string;
  owner_id: string;
  owner_name: string | null;
  owner_email: string | null;
  activated_by: string;
  contact_name: string | null;
  contact_email: string | null;
  status: EmergencyStatus;
  reason: string | null;
  grace_end_at: string;
  responded_at: string | null;
  activated_at: string;
  created_at: string;
  updated_at: string;
};

export type EmergencyReleaseItem = {
  vault_id: string;
  vault_name: string;
  item_id: string;
  item_type: string;
  title: string;
  content: Record<string, unknown>;
  updated_at: string;
};

export function listEmergencies(): Promise<Emergency[]> {
  return apiGet<Emergency[]>("/emergencies");
}

export function listActivated(): Promise<Emergency[]> {
  return apiGet<Emergency[]>("/emergencies/activated");
}

export function activateEmergency(ownerId: string, reason?: string): Promise<Emergency> {
  return apiPost<Emergency>("/emergencies", { owner_id: ownerId, reason });
}

export function confirmEmergency(id: string): Promise<Emergency> {
  return apiPost<Emergency>(`/emergencies/${id}/confirm`);
}

export function cancelEmergency(id: string): Promise<Emergency> {
  return apiPost<Emergency>(`/emergencies/${id}/cancel`);
}

export function releaseVault(id: string): Promise<EmergencyReleaseItem[]> {
  return apiGet<EmergencyReleaseItem[]>(`/emergencies/${id}/release`);
}
