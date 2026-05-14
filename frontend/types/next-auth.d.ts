import { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    tenantId: string;
    plan: string;
    industryPlugin: string;
    user: {
      id: string;
      role: string;
    } & DefaultSession["user"];
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    userId: string;
    tenantId: string;
    plan: string;
    industryPlugin: string;
    role: string;
  }
}
