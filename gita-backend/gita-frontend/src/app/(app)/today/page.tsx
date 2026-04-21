import type { Metadata } from "next";
import { TodayView } from "@/components/practice/TodayView";

export const metadata: Metadata = {
  title: "Daily verse",
};

export default function TodayPage() {
  return <TodayView />;
}
