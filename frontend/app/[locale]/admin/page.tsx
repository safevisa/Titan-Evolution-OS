import { redirect } from "next/navigation";
import { auth } from "@/auth";
import { AdminConsole, type AdminLabels } from "@/components/AdminConsole";
import { getDictionary } from "@/lib/i18n/get-dictionary";

type AppDict = { admin: AdminLabels };

export default async function AdminPage({ params }: { params: { locale: string } }) {
  const session = await auth();
  if (!session?.user?.id || session.user.role !== "platform_admin") {
    redirect(`/${params.locale}/dashboard`);
  }
  const dict = (await getDictionary(params.locale)) as { app: AppDict };
  return <AdminConsole labels={dict.app.admin} />;
}
