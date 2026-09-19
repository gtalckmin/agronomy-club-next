import api from "./api";

export type MemberProfile = {
  id: number;
  full_name: string;
  grad_yr: number | null;
  discipline: string;
  email: string;
  global_role: "admin" | "alumni" | "user";
};

export type MemberProfileInput = {
  fullName: string;
  graduationYear: string;
  discipline: string;
};

export function profileNeedsCompletion(profile: MemberProfile): boolean {
  return (
    !profile.full_name.trim() ||
    profile.grad_yr === null ||
    !profile.discipline.trim()
  );
}

function withAuthorization(idToken: string) {
  return { headers: { Authorization: `Bearer ${idToken}` } };
}

function profilePayload(input: MemberProfileInput) {
  return {
    full_name: input.fullName.trim(),
    grad_yr: Number(input.graduationYear),
    discipline: input.discipline.trim(),
  };
}

export async function getMemberProfile(
  idToken: string,
): Promise<MemberProfile> {
  const response = await api.get<MemberProfile>(
    "/member-profile/",
    withAuthorization(idToken),
  );
  return response.data;
}

export async function createMemberProfile(
  idToken: string,
  input: MemberProfileInput,
): Promise<MemberProfile> {
  const response = await api.post<MemberProfile>(
    "/member-profile/",
    profilePayload(input),
    withAuthorization(idToken),
  );
  return response.data;
}

export async function updateMemberProfile(
  idToken: string,
  input: MemberProfileInput,
): Promise<MemberProfile> {
  const response = await api.patch<MemberProfile>(
    "/member-profile/",
    profilePayload(input),
    withAuthorization(idToken),
  );
  return response.data;
}
