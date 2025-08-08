import React from "react";
import {
  FileText,
  Calendar,
  DollarSign,
  RefreshCw,
  Users,
  AlertTriangle,
  Scale,
  Building,
  Loader2,
} from "lucide-react";
import { ClauseItem } from "../types/customTypes";

interface ClauseOverviewProps {
  analyzedClauses: ClauseItem[];
  loading: boolean;
  documentId?: string;
  summary: string;
  showSummary: boolean;
}

const ClauseOverview: React.FC<ClauseOverviewProps> = ({
  analyzedClauses,
  loading,
  documentId,
  summary,
  showSummary,
}) => {
  // Icon mapping for backend clause types
  const iconMapping: { [key: string]: React.ComponentType<any> } = {
    calendar: Calendar,
    dollar: DollarSign,
    settings: Building,
    users: Users,
    alert: AlertTriangle,
    scale: Scale,
    book: FileText,
    document: FileText,
    refresh: RefreshCw,
  };

  const getIcon = (iconName: string) => {
    const IconComponent = iconMapping[iconName] || FileText;
    return IconComponent;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      <div className="p-6 border-b">
        <h3 className="text-lg font-semibold text-gray-900">
          Clause Overview
        </h3>
      </div>

      <div className="p-6 space-y-4">
        {loading ? (
          <div className="text-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-500">Analyzing clauses...</p>
          </div>
        ) : (
          <>
            {analyzedClauses.map((clause, index) => {
              const IconComponent = getIcon(clause.icon);
              return (
                <div key={index} className="flex items-start gap-3">
                  <div className="p-2 bg-gray-100 rounded-lg">
                    <IconComponent className="w-4 h-4 text-gray-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 text-sm">
                      {clause.title}
                    </div>
                    <div className="text-xs text-gray-500">{clause.subtitle}</div>
                  </div>
                </div>
              );
            })}

            {analyzedClauses.length === 0 && !loading && (
              <div className="text-center py-8 text-gray-500">
                <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">
                  {documentId ? "No clauses identified" : "Enter contract text to analyze clauses"}
                </p>
              </div>
            )}
          </>
        )}
      </div>

      {/* Summary */}
      {showSummary && (
        <div className="border-t">
          <div className="p-6">
            <h4 className="font-semibold text-gray-900 mb-3">Summary</h4>
            <p className="text-sm text-gray-700 leading-relaxed">
              {summary}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClauseOverview;
