import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRegister } from "../hooks/useRegister";
import { registerSchema, type RegisterFormValues } from "../lib/validation";
import FormField from "./FormField";

interface RegisterFormProps {
  onSuccess: (email: string) => void;
}

export default function RegisterForm({ onSuccess }: RegisterFormProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [emailConflictError, setEmailConflictError] = useState<string | null>(
    null
  );
  const [generalError, setGeneralError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    mode: "onBlur",
  });

  const mutation = useRegister();

  function clearServerErrors() {
    setEmailConflictError(null);
    setGeneralError(null);
  }

  function onSubmit(values: RegisterFormValues) {
    clearServerErrors();
    mutation.mutate(values, {
      onSuccess: (data) => {
        onSuccess(data.email);
      },
      onError: (err) => {
        if (err.status === 409) {
          setEmailConflictError(err.message);
        } else if (err.status === 400) {
          setGeneralError(err.message);
        } else {
          setGeneralError("Unexpected error, please try again.");
        }
      },
    });
  }

  const isLoading = mutation.isPending;

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      className="w-full space-y-5"
    >
      {/* General error banner */}
      {generalError && (
        <div
          role="alert"
          className="flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3"
        >
          <span className="material-symbols-outlined text-red-400 text-xl mt-0.5 flex-shrink-0">
            warning
          </span>
          <p className="text-sm text-red-300">{generalError}</p>
        </div>
      )}

      {/* Email */}
      <FormField
        id="email"
        label="Work Email"
        icon="mail"
        type="email"
        placeholder="name@enterprise.com"
        autoComplete="email"
        error={errors.email?.message ?? emailConflictError ?? undefined}
        {...register("email", {
          onChange: () => {
            if (emailConflictError) setEmailConflictError(null);
          },
        })}
      />

      {/* Password */}
      <FormField
        id="password"
        label="Password"
        icon="lock"
        type={showPassword ? "text" : "password"}
        placeholder="Min. 8 characters"
        autoComplete="new-password"
        error={errors.password?.message}
        rightSlot={
          <button
            type="button"
            aria-label={showPassword ? "Hide password" : "Show password"}
            onClick={() => setShowPassword((v: boolean) => !v)}
            className="text-slate-500 hover:text-slate-300 transition-colors"
          >
            <span className="material-symbols-outlined text-xl">
              {showPassword ? "visibility_off" : "visibility"}
            </span>
          </button>
        }
        {...register("password")}
      />

      {/* Name row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <FormField
          id="firstName"
          label="First Name"
          icon="person"
          type="text"
          placeholder="John"
          autoComplete="given-name"
          error={errors.firstName?.message}
          {...register("firstName")}
        />
        <FormField
          id="lastName"
          label="Last Name"
          icon="person"
          type="text"
          placeholder="Doe"
          autoComplete="family-name"
          error={errors.lastName?.message}
          {...register("lastName")}
        />
      </div>

      {/* Mobile */}
      <FormField
        id="mobileNumber"
        label="Mobile Number"
        icon="phone"
        type="tel"
        placeholder="+1234567890"
        autoComplete="tel"
        error={errors.mobileNumber?.message}
        {...register("mobileNumber")}
      />

      {/* Address */}
      <FormField
        id="address"
        label="Address"
        icon="home"
        type="text"
        placeholder="123 Main St, City, Country"
        autoComplete="street-address"
        error={errors.address?.message}
        {...register("address")}
      />

      {/* Submit */}
      <div className="pt-2">
        <button
          type="submit"
          disabled={isLoading}
          className="w-full h-14 bg-primary hover:bg-primary/90 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed disabled:active:scale-100 text-white font-bold rounded-xl transition-all shadow-lg shadow-primary/25 flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <span className="material-symbols-outlined text-xl animate-spin">
                progress_activity
              </span>
              <span>Creating account…</span>
            </>
          ) : (
            <>
              <span>Create Account</span>
              <span className="material-symbols-outlined text-xl">
                person_add
              </span>
            </>
          )}
        </button>
      </div>
    </form>
  );
}
