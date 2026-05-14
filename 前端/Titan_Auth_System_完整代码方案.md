# Titan Evolution OS — 登录系统完整代码方案

## 技术选型

- **框架**: Next.js 14 App Router
- **认证库**: NextAuth.js v5 (Auth.js)
- **提供商**: Google OAuth + 邮箱/密码
- **数据库**: PostgreSQL (已有) + Prisma ORM
- **Session**: JWT (存 tenant_id / user_id / plan)
- **中间件**: Next.js Middleware 路由保护

---

## 1. 安装依赖

```bash
npm install next-auth@beta @auth/prisma-adapter prisma bcryptjs
npm install -D @types/bcryptjs
```

---

## 2. 数据库 Schema (Prisma)

```prisma
// prisma/schema.prisma

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id            String    @id @default(cuid())
  name          String?
  email         String    @unique
  emailVerified DateTime?
  image         String?
  passwordHash  String?   // 邮箱登录用
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt

  // 关联
  accounts      Account[]
  sessions      Session[]
  tenant        Tenant?   @relation(fields: [tenantId], references: [id])
  tenantId      String?   @unique  // 一个用户对应一个租户
}

model Account {
  id                String  @id @default(cuid())
  userId            String
  type              String
  provider          String
  providerAccountId String
  refresh_token     String? @db.Text
  access_token      String? @db.Text
  expires_at        Int?
  token_type        String?
  scope             String?
  id_token          String? @db.Text
  session_state     String?

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@unique([provider, providerAccountId])
}

model Session {
  id           String   @id @default(cuid())
  sessionToken String   @unique
  userId       String
  expires      DateTime
  user         User     @relation(fields: [userId], references: [id], onDelete: Cascade)
}

model VerificationToken {
  identifier String
  token      String   @unique
  expires    DateTime

  @@unique([identifier, token])
}

// 已有的 Tenant 表，加上 User 关联
model Tenant {
  id             String   @id @default(cuid())
  name           String
  industryPlugin String
  plan           String   @default("starter")
  config         Json     @default("{}")
  createdAt      DateTime @default(now())

  user User? // 反向关联
}
```

---

## 3. NextAuth 配置

```typescript
// auth.ts (项目根目录)

import NextAuth from "next-auth"
import { PrismaAdapter } from "@auth/prisma-adapter"
import Google from "next-auth/providers/google"
import Credentials from "next-auth/providers/credentials"
import { prisma } from "@/lib/prisma"
import bcrypt from "bcryptjs"

export const { handlers, signIn, signOut, auth } = NextAuth({
  adapter: PrismaAdapter(prisma),

  providers: [
    // Google OAuth
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),

    // 邮箱 + 密码
    Credentials({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null

        const user = await prisma.user.findUnique({
          where: { email: credentials.email as string },
        })

        if (!user || !user.passwordHash) return null

        const valid = await bcrypt.compare(
          credentials.password as string,
          user.passwordHash
        )

        return valid ? user : null
      },
    }),
  ],

  session: { strategy: "jwt" },

  callbacks: {
    // JWT 里注入 tenantId 和 plan
    async jwt({ token, user }) {
      if (user) {
        // 首次登录：查询或自动创建 Tenant
        const dbUser = await prisma.user.findUnique({
          where: { id: user.id },
          include: { tenant: true },
        })

        if (!dbUser?.tenant) {
          // 新用户自动创建 Starter Tenant
          const tenant = await prisma.tenant.create({
            data: {
              name: `${user.name || user.email}'s Workspace`,
              industryPlugin: "payment_fintech",
              plan: "starter",
              user: { connect: { id: user.id! } },
            },
          })
          token.tenantId = tenant.id
          token.plan = tenant.plan
          token.industryPlugin = tenant.industryPlugin
        } else {
          token.tenantId = dbUser.tenant.id
          token.plan = dbUser.tenant.plan
          token.industryPlugin = dbUser.tenant.industryPlugin
        }

        token.userId = user.id
      }
      return token
    },

    // Session 里暴露给前端
    async session({ session, token }) {
      session.user.id = token.userId as string
      session.tenantId = token.tenantId as string
      session.plan = token.plan as string
      session.industryPlugin = token.industryPlugin as string
      return session
    },
  },

  pages: {
    signIn: "/login",      // 自定义登录页
    error: "/login",       // 错误重定向
    newUser: "/onboarding", // 新用户引导
  },
})
```

---

## 4. TypeScript 类型扩展

```typescript
// types/next-auth.d.ts

import { DefaultSession } from "next-auth"

declare module "next-auth" {
  interface Session {
    tenantId: string
    plan: string
    industryPlugin: string
    user: {
      id: string
    } & DefaultSession["user"]
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    userId: string
    tenantId: string
    plan: string
    industryPlugin: string
  }
}
```

---

## 5. 路由保护中间件

```typescript
// middleware.ts (项目根目录)

import { auth } from "@/auth"
import { NextResponse } from "next/server"

// 需要登录才能访问的路由
const PROTECTED_ROUTES = [
  "/dashboard",
  "/agents",
  "/tasks",
  "/evolution",
  "/skills",
  "/billing",
  "/settings",
  "/onboarding",
]

// 已登录用户不应访问的路由
const AUTH_ROUTES = ["/login", "/register"]

export default auth((req) => {
  const { pathname } = req.nextUrl
  const isLoggedIn = !!req.auth

  const isProtected = PROTECTED_ROUTES.some(r => pathname.startsWith(r))
  const isAuthRoute = AUTH_ROUTES.some(r => pathname.startsWith(r))

  // 未登录访问受保护路由 → 跳转登录
  if (isProtected && !isLoggedIn) {
    const loginUrl = new URL("/login", req.url)
    loginUrl.searchParams.set("callbackUrl", pathname)
    return NextResponse.redirect(loginUrl)
  }

  // 已登录访问登录页 → 跳转 dashboard
  if (isAuthRoute && isLoggedIn) {
    return NextResponse.redirect(new URL("/dashboard", req.url))
  }

  return NextResponse.next()
})

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
}
```

---

## 6. 注册 API

```typescript
// app/api/auth/register/route.ts

import { NextResponse } from "next/server"
import { prisma } from "@/lib/prisma"
import bcrypt from "bcryptjs"
import { z } from "zod"

const schema = z.object({
  name: z.string().min(2, "名字至少2个字符"),
  email: z.string().email("邮箱格式不正确"),
  password: z.string().min(8, "密码至少8位"),
})

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { name, email, password } = schema.parse(body)

    // 检查邮箱是否已注册
    const existing = await prisma.user.findUnique({ where: { email } })
    if (existing) {
      return NextResponse.json(
        { error: "该邮箱已注册" },
        { status: 400 }
      )
    }

    // 加密密码
    const passwordHash = await bcrypt.hash(password, 12)

    // 创建用户
    const user = await prisma.user.create({
      data: { name, email, passwordHash },
    })

    return NextResponse.json({ success: true, userId: user.id })
  } catch (err) {
    if (err instanceof z.ZodError) {
      return NextResponse.json({ error: err.errors[0].message }, { status: 400 })
    }
    return NextResponse.json({ error: "注册失败" }, { status: 500 })
  }
}
```

---

## 7. 后端 API — 自动注入 tenantId

```typescript
// lib/api-auth.ts
// 所有后端 API 用这个工具函数，彻底消灭手动传 UUID

import { auth } from "@/auth"
import { NextResponse } from "next/server"

export async function withAuth(
  handler: (tenantId: string, userId: string, req: Request) => Promise<Response>
) {
  return async (req: Request) => {
    const session = await auth()

    if (!session?.tenantId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    return handler(session.tenantId, session.user.id, req)
  }
}

// 用法示例：
// app/api/agents/route.ts
import { withAuth } from "@/lib/api-auth"

export const GET = withAuth(async (tenantId, userId, req) => {
  const agents = await prisma.agent.findMany({
    where: { tenantId },  // 自动用 session 里的 tenantId，用户完全感知不到
  })
  return NextResponse.json(agents)
})
```

---

## 8. 前端 Hook — 获取当前用户

```typescript
// hooks/useAuth.ts

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect } from "react"

export function useAuth(requireAuth = true) {
  const { data: session, status } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (requireAuth && status === "unauthenticated") {
      router.push("/login")
    }
  }, [status, requireAuth, router])

  return {
    user: session?.user,
    tenantId: session?.tenantId,  // 直接用，不需要手动传
    plan: session?.plan,
    industryPlugin: session?.industryPlugin,
    isLoading: status === "loading",
    isAuthenticated: status === "authenticated",
  }
}

// 用法（任何页面）：
// const { user, tenantId, plan } = useAuth()
// → tenantId 自动从 session 取，永远不需要用户手动输入
```

---

## 9. Onboarding 流程（新用户自动引导）

```typescript
// app/onboarding/page.tsx

"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/hooks/useAuth"

const STEPS = ["行业选择", "团队初始化", "第一个目标", "完成"]

export default function OnboardingPage() {
  const { tenantId } = useAuth()
  const router = useRouter()
  const [step, setStep] = useState(0)
  const [industry, setIndustry] = useState("payment_fintech")
  const [loading, setLoading] = useState(false)

  async function handleFinish(firstGoal: string) {
    setLoading(true)

    // 1. 更新行业插件
    await fetch(`/api/tenants/${tenantId}`, {
      method: "PATCH",
      body: JSON.stringify({ industryPlugin: industry }),
    })

    // 2. 自动创建默认4个Agent（后端seed）
    await fetch(`/api/tenants/${tenantId}/provision`, {
      method: "POST",
    })

    // 3. 自动创建第一个任务
    await fetch("/api/tasks", {
      method: "POST",
      body: JSON.stringify({
        // tenantId 从 session 自动带，不需要前端传
        type: "lead_search",
        input: { goal: firstGoal, industry },
      }),
    })

    router.push("/dashboard?welcome=1")
  }

  // ... 步骤 UI 渲染
}
```

---

## 10. 环境变量配置

```bash
# .env.local

# 数据库
DATABASE_URL="postgresql://..."

# NextAuth
AUTH_SECRET="your-32-char-secret"  # openssl rand -base64 32

# Google OAuth
# 在 console.cloud.google.com 创建 OAuth 2.0 Client
# 授权回调 URI: http://localhost:3000/api/auth/callback/google
GOOGLE_CLIENT_ID="..."
GOOGLE_CLIENT_SECRET="..."

# 应用 URL
NEXTAUTH_URL="http://localhost:3000"
```

---

## 11. 页面路由结构

```
app/
├── (auth)/                    # 未登录区域（无 layout header）
│   ├── login/page.tsx
│   └── register/page.tsx
│
├── (app)/                     # 登录后区域（有 sidebar + header）
│   ├── layout.tsx             # 主 layout：sidebar + session provider
│   ├── dashboard/page.tsx
│   ├── agents/
│   │   ├── page.tsx           # Agent 列表
│   │   └── [id]/page.tsx      # Agent 详情
│   ├── tasks/page.tsx
│   ├── evolution/page.tsx
│   ├── skills/page.tsx
│   ├── billing/page.tsx
│   └── settings/page.tsx
│
└── onboarding/page.tsx        # 新用户引导（独立 layout）
```

---

## 关键改变总结

| 改变前 | 改变后 |
|--------|--------|
| 每页手动输入 UUID | Session 自动携带 tenantId |
| 无登录态 | JWT Session，刷新不丢失 |
| 所有人共享数据 | 每个用户只能看到自己的数据 |
| Dashboard 是调试界面 | 首次进入触发 Onboarding |
| 后端 API 无鉴权 | withAuth 中间件统一保护 |
| 无注册流程 | Google OAuth + 邮箱注册 |
