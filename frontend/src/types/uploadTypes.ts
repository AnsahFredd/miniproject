import { LucideIcon } from "lucide-react";

export interface ClauseItem {
  icon: LucideIcon;
  title: string;
  subtitle: string;
  value: string;
}

export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  status: "uploaded" | "processing" | "completed" | "error";
  content?: string;
}
