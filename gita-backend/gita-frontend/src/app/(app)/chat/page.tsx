import type { Metadata } from "next";
import { GuidanceApp } from "@/components/guidance/GuidanceApp";

export const metadata: Metadata = {
  title: "Reflect",
};

export default function ChatPage() {
  return <GuidanceApp variant="companion" />;
}
