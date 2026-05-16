import { Suspense } from "react";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { TaskListConsole, type TaskListLabels } from "@/components/TaskListConsole";

export default async function TasksPage({ params }: { params: { locale: string } }) {
  const dict = await getDictionary(params.locale);
  const app = dict.app as Record<string, unknown>;
  return (
    <Suspense fallback={null}>
      <TaskListConsole labels={app.tasksPage as TaskListLabels} />
    </Suspense>
  );
}
