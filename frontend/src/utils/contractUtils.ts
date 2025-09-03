// contractUtils.ts
import {
  Calendar,
  DollarSign,
  RefreshCw,
  Users,
  AlertTriangle,
  Scale,
  Building,
  FileText,
} from "lucide-react";

export interface ClauseItem {
  icon: React.ComponentType<any>;
  title: string;
  subtitle: string;
  value: string;
}

export const analyzeContract = (text: string): ClauseItem[] => {
  const clauses: ClauseItem[] = [];

  const patterns = [
    {
      name: "Lease Term",
      icon: Calendar,
      regex: [/term\s+of\s+(\d+)[\s-]*year/gi],
      format: (match: string) => `${match} year${parseInt(match) > 1 ? 's' : ''}`,
    },
    {
      name: "Rent Amount",
      icon: DollarSign,
      regex: [/\$([0-9,]+)[\s\/]*(?:per\s+)?month/gi],
      format: (match: string) => `$${parseInt(match.replace(/,/g, '')).toLocaleString()}/month`,
    },
    {
      name: "Renewal Option",
      icon: RefreshCw,
      regex: [/renew.*?(\d+)[\s-]*year/gi],
      format: (match: string) => `${match} year${parseInt(match) > 1 ? 's' : ''}`,
    },
  ];

  for (const pattern of patterns) {
    for (const reg of pattern.regex) {
      const match = reg.exec(text);
      if (match && match[1]) {
        clauses.push({
          icon: pattern.icon,
          title: pattern.format(match[1]),
          subtitle: pattern.name,
          value: match[1],
        });
        break;
      }
    }
  }

  const checks = [
    {
      regex: /shared.*?maintenance|both\s+parties.*?maintenance/gi,
      clause: {
        icon: Users,
        title: "Shared",
        subtitle: "Maintenance",
        value: "shared",
      },
    },
    {
      regex: /tenant.*?improvement/gi,
      clause: {
        icon: Building,
        title: "Tenant",
        subtitle: "Improvements",
        value: "allowed",
      },
    },
    {
      regex: /early\s+termination|terminate.*?early/gi,
      clause: {
        icon: AlertTriangle,
        title: "Conditions Apply",
        subtitle: "Early Termination",
        value: "conditions",
      },
    },
    {
      regex: /dispute\s+resolution|mediation|arbitration/gi,
      clause: {
        icon: Scale,
        title: "Mediation",
        subtitle: "Dispute Resolution",
        value: "mediation",
      },
    },
    {
      regex: /local\s+regulation|compliance.*?local/gi,
      clause: {
        icon: FileText,
        title: "Local Regulations",
        subtitle: "Compliance",
        value: "required",
      },
    },
  ];

  for (const { regex, clause } of checks) {
    if (regex.test(text)) {
      clauses.push(clause);
    }
  }

  return clauses;
};
