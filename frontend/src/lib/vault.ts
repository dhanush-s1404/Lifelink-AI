import { apiDelete, apiGet, apiPatch, apiPost } from "./api";

export type ItemType =
  | "document"
  | "note"
  | "financial"
  | "insurance"
  | "medical"
  | "legal"
  | "emergency"
  | "contact"
  | "digital_asset";

export type Vault = {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Category = {
  id: string;
  vault_id: string;
  name: string;
  sort_order: number;
};

export type VaultItem = {
  id: string;
  vault_id: string;
  category_id: string | null;
  item_type: ItemType;
  title: string;
  masked_summary: string | null;
  is_archived: boolean;
  version: number;
  created_at: string;
  updated_at: string;
};

export type VaultItemDetail = VaultItem & {
  content: Record<string, unknown>;
};

export const ITEM_TYPES: { value: ItemType; label: string }[] = [
  { value: "document", label: "Document" },
  { value: "note", label: "Note" },
  { value: "financial", label: "Financial" },
  { value: "insurance", label: "Insurance" },
  { value: "medical", label: "Medical" },
  { value: "legal", label: "Legal" },
  { value: "emergency", label: "Emergency" },
  { value: "contact", label: "Contact" },
  { value: "digital_asset", label: "Digital asset" },
];

export function itemTypeLabel(value: ItemType): string {
  return ITEM_TYPES.find((t) => t.value === value)?.label ?? value;
}

export function listVaults(): Promise<Vault[]> {
  return apiGet<Vault[]>("/vaults");
}

export function createVault(body: { name: string; description?: string }): Promise<Vault> {
  return apiPost<Vault>("/vaults", body);
}

export function deleteVault(id: string): Promise<void> {
  return apiDelete(`/vaults/${id}`);
}

export function listCategories(vaultId: string): Promise<Category[]> {
  return apiGet<Category[]>(`/vaults/${vaultId}/categories`);
}

export function listItems(vaultId: string): Promise<VaultItem[]> {
  return apiGet<VaultItem[]>(`/vaults/${vaultId}/items`);
}

export function getItem(vaultId: string, itemId: string): Promise<VaultItemDetail> {
  return apiGet<VaultItemDetail>(`/vaults/${vaultId}/items/${itemId}`);
}

export function createItem(
  vaultId: string,
  body: {
    item_type: ItemType;
    title: string;
    content: Record<string, unknown>;
    category_id?: string;
    masked_summary?: string;
  }
): Promise<VaultItemDetail> {
  return apiPost<VaultItemDetail>(`/vaults/${vaultId}/items`, body);
}

export function updateItem(
  vaultId: string,
  itemId: string,
  body: {
    title?: string;
    content?: Record<string, unknown>;
    masked_summary?: string;
    is_archived?: boolean;
  }
): Promise<VaultItemDetail> {
  return apiPatch<VaultItemDetail>(`/vaults/${vaultId}/items/${itemId}`, body);
}

export function deleteItem(vaultId: string, itemId: string): Promise<void> {
  return apiDelete(`/vaults/${vaultId}/items/${itemId}`);
}
