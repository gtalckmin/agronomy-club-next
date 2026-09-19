export type RegistrationValues = {
  fullName: string;
  graduationYear: string;
  discipline: string;
  password: string;
  confirmPassword: string;
};

export type RegistrationErrors = Partial<
  Record<keyof RegistrationValues | "email", string>
>;

export function validateRegistration(
  values: RegistrationValues,
): RegistrationErrors {
  const errors: RegistrationErrors = {};
  if (!values.fullName.trim()) errors.fullName = "Enter your full name.";
  if (!values.graduationYear)
    errors.graduationYear = "Choose your graduation year.";
  if (!values.discipline.trim()) errors.discipline = "Enter your discipline.";
  if (values.password.length < 8)
    errors.password = "Use at least 8 characters.";
  if (values.password !== values.confirmPassword) {
    errors.confirmPassword = "Passwords do not match.";
  }
  return errors;
}
