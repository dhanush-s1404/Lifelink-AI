import { apiDelete, apiGet, apiPatch, apiPost } from "./api";

export type ContactStatus = "pending" | "active";

export type Contact = {
  id: string;
  status: ContactStatus;
  contact_id: string;
  contact_email: string | null;
  contact_name: string | null;
  can_activate_emergency: boolean;
  can_view_vaults: boolean;
  access_grace_days: number;
  created_at: string;
  updated_at: string;
};

export type ContactInviteBody = {
  email: string;
  can_activate_emergency?: boolean;
  can_view_vaults?: boolean;
  access_grace_days?: number;
};

export function listContacts(): Promise<Contact[]> {
  return apiGet<Contact[]>("/contacts");
}

export function listIncoming(): Promise<Contact[]> {
  return apiGet<Contact[]>("/contacts/incoming");
}

export function inviteContact(body: ContactInviteBody): Promise<Contact> {
  return apiPost<Contact>("/contacts", body);
}

export function acceptContact(id: string): Promise<Contact> {
  return apiPost<Contact>(`/contacts/${id}/accept`);
}

export function declineContact(id: string): Promise<void> {
  return apiPost<void>(`/contacts/${id}/decline`);
}

export function removeContact(id: string): Promise<void> {
  return apiDelete(`/contacts/${id}`);
}

export function updateContact(
  id: string,
  body: { can_activate_emergency?: boolean; can_view_vaults?: boolean; access_grace_days?: number }
): Promise<Contact> {
  return apiPatch<Contact>(`/contacts/${id}`, body);
}
