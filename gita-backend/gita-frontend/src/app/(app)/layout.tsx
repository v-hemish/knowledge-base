import type { ReactNode } from "react";
import { PracticeLayoutClient } from "@/components/shell/PracticeLayoutClient";

export default function AppSectionLayout({ children }: { children: ReactNode }) {
  return <PracticeLayoutClient>{children}</PracticeLayoutClient>;
}
