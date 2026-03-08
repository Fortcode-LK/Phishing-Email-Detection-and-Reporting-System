import { z } from "zod";

export const registerSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Enter a valid email address"),

  password: z
    .string()
    .min(1, "Password is required")
    .min(8, "Password must be at least 8 characters"),

  firstName: z
    .string()
    .max(50, "First name must be at most 50 characters")
    .optional()
    .or(z.literal("")),

  lastName: z
    .string()
    .max(50, "Last name must be at most 50 characters")
    .optional()
    .or(z.literal("")),

  mobileNumber: z
    .string()
    .regex(
      /^[+\d]{8,15}$/,
      "Mobile number must be 8–15 digits and may start with +"
    )
    .optional()
    .or(z.literal("")),

  address: z
    .string()
    .max(200, "Address must be at most 200 characters")
    .optional()
    .or(z.literal("")),
});

export type RegisterFormValues = z.infer<typeof registerSchema>;
