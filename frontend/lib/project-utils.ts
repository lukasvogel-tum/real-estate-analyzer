import type { ProjectInfo, ProjectType } from "@/lib/types";


export function normalizeProjectType(projectType: ProjectType | string): "bestand" | "geplant" {
  return projectType === "bestand" ? "bestand" : "geplant";
}


export function getProjectTypeLabel(projectType: ProjectType | string): string {
  return normalizeProjectType(projectType) === "bestand" ? "Bestand" : "Geplant";
}


export function isPlannedProject(project: ProjectInfo): boolean {
  return normalizeProjectType(project.project_type) === "geplant";
}
