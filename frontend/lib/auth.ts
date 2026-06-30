import type { CurrentUserResponse, UserRole } from "@/lib/types";

const ROLE_RANK: Record<UserRole, number> = {
  user: 1,
  kb_manager: 2,
  admin: 3,
};

export function hasRoleAtLeast(
  currentUser: CurrentUserResponse | null | undefined,
  role: UserRole
): boolean {
  if (!currentUser) {
    return false;
  }
  return ROLE_RANK[currentUser.role] >= ROLE_RANK[role];
}

export function canManageKnowledge(
  currentUser: CurrentUserResponse | null | undefined
): boolean {
  return hasRoleAtLeast(currentUser, "kb_manager");
}

export function canAdminister(
  currentUser: CurrentUserResponse | null | undefined
): boolean {
  return hasRoleAtLeast(currentUser, "admin");
}
