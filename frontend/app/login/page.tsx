"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ThemeToggle } from "@/components/theme-toggle";
import { login, register } from "@/services/auth-service";

const signInSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Minimum 8 characters")
});

const signUpSchema = z
  .object({
    fullName: z.string().min(2, "Full name is required"),
    email: z.string().email("Enter a valid email"),
    password: z.string().min(8, "Minimum 8 characters"),
    confirmPassword: z.string().min(8, "Minimum 8 characters")
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"]
  });

type SignInValues = z.infer<typeof signInSchema>;
type SignUpValues = z.infer<typeof signUpSchema>;

export default function LoginPage() {
  const router = useRouter();
  const [shake, setShake] = useState(false);
  const [mode, setMode] = useState<"signin" | "signup">("signin");

  const {
    register: registerSignIn,
    handleSubmit: handleSubmitSignIn,
    formState: { errors: signInErrors, isSubmitting: isSigningIn }
  } = useForm<SignInValues>({
    resolver: zodResolver(signInSchema)
  });

  const {
    register: registerSignUp,
    handleSubmit: handleSubmitSignUp,
    formState: { errors: signUpErrors, isSubmitting: isSigningUp }
  } = useForm<SignUpValues>({
    resolver: zodResolver(signUpSchema)
  });

  const onSignInSubmit = async (values: SignInValues) => {
    try {
      const response = await login(values.email, values.password);
      localStorage.setItem("resume-analyzer-token", response.token);
      router.push("/dashboard");
    } catch {
      setShake(true);
      setTimeout(() => setShake(false), 500);
    }
  };

  const onSignUpSubmit = async (values: SignUpValues) => {
    try {
      const response = await register({
        fullName: values.fullName,
        email: values.email,
        password: values.password
      });

      localStorage.setItem("resume-analyzer-token", response.token);
      localStorage.setItem("resume-analyzer-name", values.fullName);

      router.push("/onboarding");
    } catch {
      setShake(true);
      setTimeout(() => setShake(false), 500);
    }
  };

  return (
    <main className="grid min-h-screen lg:grid-cols-2">
      <section className="relative hidden overflow-hidden bg-gradient-to-br from-indigo-500 to-cyan-400 lg:block">
        <div className="absolute inset-0 bg-black/10" />
        <motion.div
          animate={{ y: [0, -15, 0] }}
          transition={{ duration: 5, repeat: Infinity }}
          className="absolute left-12 top-20 h-56 w-56 rounded-full bg-white/20 blur-2xl"
        />
        <div className="relative z-10 flex h-full flex-col justify-end p-12 text-white">
          <h1 className="text-4xl font-semibold">Turn resumes into clear, actionable career intelligence.</h1>
          <p className="mt-4 max-w-md text-white/85">AI-powered matching, animated dashboards, and role-focused growth plans in one premium platform.</p>
        </div>
      </section>

      <section className="relative flex items-center justify-center p-6">
        <div className="absolute right-6 top-6"><ThemeToggle /></div>
        <motion.form
          onSubmit={
            mode === "signin"
              ? handleSubmitSignIn(onSignInSubmit)
              : handleSubmitSignUp(onSignUpSubmit)
          }
          animate={shake ? { x: [-12, 12, -8, 8, 0] } : { x: 0 }}
          className="glass-card w-full max-w-xl space-y-6 p-8 sm:p-10"
        >
          <AnimatePresence mode="wait">
            {mode === "signin" ? (
              <motion.div
                key="signin"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.25 }}
                className="space-y-6 rounded-xl border border-border/60 bg-background/40 p-6"
              >
                <div>
                  <h2 className="text-2xl font-semibold">Welcome back</h2>
                  <p className="text-sm text-muted-foreground">Sign in to continue your resume analysis.</p>
                </div>
                <div className="space-y-2.5">
                  <label className="text-sm font-medium">Email</label>
                  <Input {...registerSignIn("email")} placeholder="you@company.com" />
                  {signInErrors.email && <p className="text-xs text-red-500">{signInErrors.email.message}</p>}
                </div>
                <div className="space-y-2.5">
                  <label className="text-sm font-medium">Password</label>
                  <Input type="password" {...registerSignIn("password")} placeholder="••••••••" />
                  {signInErrors.password && <p className="text-xs text-red-500">{signInErrors.password.message}</p>}
                </div>
                <Button className="w-full py-6" disabled={isSigningIn}>Continue</Button>
              </motion.div>
            ) : (
              <motion.div
                key="signup"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.25 }}
                className="space-y-5 rounded-xl border border-border/60 bg-background/40 p-6"
              >
                <div>
                  <h2 className="text-2xl font-semibold">Create your account</h2>
                  <p className="text-sm text-muted-foreground">Create your account. We’ll ask career questions right after sign up.</p>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2.5 sm:col-span-2">
                    <label className="text-sm font-medium">Full Name</label>
                    <Input {...registerSignUp("fullName")} placeholder="Your full name" />
                    {signUpErrors.fullName && <p className="text-xs text-red-500">{signUpErrors.fullName.message}</p>}
                  </div>
                  <div className="space-y-2.5">
                    <label className="text-sm font-medium">Email</label>
                    <Input {...registerSignUp("email")} placeholder="you@company.com" />
                    {signUpErrors.email && <p className="text-xs text-red-500">{signUpErrors.email.message}</p>}
                  </div>
                  <div className="space-y-2.5">
                    <label className="text-sm font-medium">Password</label>
                    <Input type="password" {...registerSignUp("password")} placeholder="••••••••" />
                    {signUpErrors.password && <p className="text-xs text-red-500">{signUpErrors.password.message}</p>}
                  </div>
                  <div className="space-y-2.5 sm:col-span-2">
                    <label className="text-sm font-medium">Confirm Password</label>
                    <Input type="password" {...registerSignUp("confirmPassword")} placeholder="••••••••" />
                    {signUpErrors.confirmPassword && <p className="text-xs text-red-500">{signUpErrors.confirmPassword.message}</p>}
                  </div>
                </div>
                <Button className="w-full py-6" disabled={isSigningUp}>Create Account</Button>
              </motion.div>
            )}
          </AnimatePresence>

          <p className="text-center text-sm text-muted-foreground">
            {mode === "signin" ? "Don’t have an account?" : "Already have an account?"}{" "}
            <button
              type="button"
              className="font-semibold text-primary underline-offset-4 hover:underline"
              onClick={() => setMode(mode === "signin" ? "signup" : "signin")}
            >
              {mode === "signin" ? "Sign up" : "Sign in"}
            </button>
          </p>
        </motion.form>
      </section>
    </main>
  );
}
