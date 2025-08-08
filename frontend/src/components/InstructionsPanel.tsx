import React from "react";

interface InstructionsPanelProps {
  documentId?: string;
}

const InstructionsPanel: React.FC<InstructionsPanelProps> = ({ documentId }) => {
  return (
    <div className="mt-6 p-4 rounded-lg border border-[color:rgb(20_184_166_/_26%)] bg-[color:rgb(20_184_166_/_8%)]">
      <h4 className="font-medium text-[var(--color-accent)] mb-2">How it works:</h4>
      <ul className="text-sm text-[var(--color-secondary)] space-y-1">
        <li>
          • {documentId 
            ? "Document automatically loaded and analyzed from backend" 
            : "Paste any contract text into the textarea above"}
        </li>
        <li>
          • The system automatically extracts key clauses like lease terms,
          rent amounts, renewal options
        </li>
        <li>
          • The clause overview updates dynamically with actual values from
          your contract
        </li>
        <li>
          • Works with contracts of any duration, rent amount, and clause
          combinations
        </li>
      </ul>
    </div>
  );
};

export default InstructionsPanel;
