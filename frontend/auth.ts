import NextAuth from "next-auth";
import { PrismaAdapter } from "@auth/prisma-adapter";
import Google from "next-auth/providers/google";
import Credentials from "next-auth/providers/credentials";
import bcrypt from "bcryptjs";
import { prisma } from "@/lib/prisma";

const ADMIN_ROLE = "platform_admin";
const USER_ROLE = "tenant_user";

function isPlatformAdminEmail(email?: string | null) {
  if (!email) return false;
  const adminEmails = (process.env.TITAN_ADMIN_EMAILS ?? "")
    .split(",")
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
  return adminEmails.includes(email.toLowerCase());
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  trustHost: true,
  adapter: PrismaAdapter(prisma),

  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID ?? "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
    }),

    Credentials({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        const user = await prisma.user.findUnique({
          where: { email: credentials.email as string },
        });

        if (!user || !user.passwordHash) return null;

        const valid = await bcrypt.compare(
          credentials.password as string,
          user.passwordHash
        );
        return valid ? user : null;
      },
    }),
  ],

  session: { strategy: "jwt" },

  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.userId = user.id;

        // Fetch or create tenant via FastAPI backend
        const dbUser = await prisma.user.findUnique({ where: { id: user.id } });
        const role = isPlatformAdminEmail(user.email)
          ? ADMIN_ROLE
          : dbUser?.role ?? USER_ROLE;
        token.role = role;

        if (dbUser && dbUser.role !== role) {
          await prisma.user.update({
            where: { id: user.id },
            data: { role },
          });
        }

        if (!dbUser?.tenantId) {
          try {
            const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";
            const res = await fetch(`${backendUrl}/api/v1/tenants`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                name: `${user.name ?? user.email}'s Workspace`,
                industry_plugin: "payment_fintech",
                plan: "starter",
                auto_provision: true,
              }),
            });
            if (res.ok) {
              const tenant = await res.json();
              await prisma.user.update({
                where: { id: user.id },
                data: { tenantId: tenant.id },
              });
              token.tenantId = tenant.id;
              token.plan = tenant.plan;
              token.industryPlugin = tenant.industry_plugin;
            }
          } catch {
            // Backend unavailable — skip tenant creation, retry next login
          }
        } else {
          token.tenantId = dbUser.tenantId;
          // Fetch plan from backend if not cached
          if (!token.plan) {
            try {
              const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";
              const res = await fetch(`${backendUrl}/api/v1/tenants/${dbUser.tenantId}`);
              if (res.ok) {
                const t = await res.json();
                token.plan = t.plan;
                token.industryPlugin = t.industry_plugin;
              }
            } catch {
              token.plan = "starter";
            }
          }
        }
      } else if (!token.role && token.userId) {
        const dbUser = await prisma.user.findUnique({ where: { id: token.userId as string } });
        token.role = isPlatformAdminEmail(token.email) ? ADMIN_ROLE : dbUser?.role ?? USER_ROLE;
      }
      return token;
    },

    async session({ session, token }) {
      if (token) {
        session.user.id = token.userId as string;
        session.user.role = (token.role as string) ?? USER_ROLE;
        session.tenantId = token.tenantId as string;
        session.plan = (token.plan as string) ?? "starter";
        session.industryPlugin = (token.industryPlugin as string) ?? "payment_fintech";
      }
      return session;
    },
  },

  pages: {
    signIn: "/login",
    error: "/login",
  },
});
