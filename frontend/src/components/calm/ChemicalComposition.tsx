/**
 * Chemical Composition Component
 * 
 * Displays detailed chemical analysis:
 * - Formula and molecular properties
 * - Chemical structure details
 * - Similarity to approved drugs
 * - Mechanism of action and therapeutic potential
 * - Structure-activity relationships
 */

import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle2,
  Zap,
  Beaker,
  ShieldAlert,
  FlaskConical,
  Dna,
} from 'lucide-react';
import type { ChemicalCompositionResponse } from '../../types/api';
import SmilesDrawer from 'smiles-drawer';

interface ChemicalCompositionProps {
  data: ChemicalCompositionResponse;
  isLoading?: boolean;
  isExpanded?: boolean;
}

export const ChemicalComposition: React.FC<ChemicalCompositionProps> = ({
  data,
  isLoading = false,
  isExpanded: initialExpanded = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(initialExpanded);
  const structureCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const [smilesError, setSmilesError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg animate-pulse">
        <div className="h-6 bg-blue-200 rounded w-1/3 mb-4"></div>
        <div className="h-4 bg-blue-100 rounded w-full mb-2"></div>
        <div className="h-4 bg-blue-100 rounded w-5/6"></div>
      </div>
    );
  }

  if (data.error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
        <div>
          <h3 className="font-semibold text-red-900">Analysis Failed</h3>
          <p className="text-sm text-red-700 mt-1">{data.error}</p>
        </div>
      </div>
    );
  }

  const confidenceColor = {
    HIGH: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    MEDIUM: 'bg-amber-50 text-amber-700 border-amber-200',
    LOW: 'bg-rose-50 text-rose-700 border-rose-200',
  }[data.evidence_confidence];

  const summaryCards = useMemo(
    () =>
      [
        { label: 'Formula', value: data.chemical_formula, icon: <Dna className="w-4 h-4 text-blue-600" /> },
        {
          label: 'Molecular Weight',
          value: data.molecular_weight ? `${data.molecular_weight} g/mol` : undefined,
          icon: <FlaskConical className="w-4 h-4 text-blue-600" />,
        },
        {
          label: 'Similarity',
          value: data.similarity_score !== undefined ? `${(data.similarity_score * 100).toFixed(0)}%` : undefined,
          icon: <CheckCircle2 className="w-4 h-4 text-blue-600" />,
        },
        {
          label: 'Similar Drugs',
          value: data.similar_drugs?.length ? `${data.similar_drugs.length} identified` : undefined,
          icon: <Beaker className="w-4 h-4 text-blue-600" />,
        },
      ].filter((item) => Boolean(item.value)),
    [data]
  );

  const detailSections = [
    { title: 'Mechanism of Action', value: data.mechanism_of_action, icon: <Zap className="w-4 h-4 text-indigo-600" /> },
    { title: 'Therapeutic Potential', value: data.therapeutic_potential, icon: <CheckCircle2 className="w-4 h-4 text-indigo-600" /> },
    { title: 'Chemical Structure', value: data.chemical_structure, icon: <Beaker className="w-4 h-4 text-indigo-600" /> },
    { title: 'Structure Details', value: data.structure_details, icon: <Dna className="w-4 h-4 text-indigo-600" /> },
    { title: 'Pharmacophore Elements', value: data.pharmacophore_elements, icon: <FlaskConical className="w-4 h-4 text-indigo-600" /> },
    { title: 'Drug Similarity Analysis', value: data.drug_similarity_analysis, icon: <CheckCircle2 className="w-4 h-4 text-indigo-600" /> },
    { title: 'Structure-Activity Relationship', value: data.structure_activity_relationship, icon: <Zap className="w-4 h-4 text-indigo-600" /> },
    { title: 'Key Interactions', value: data.key_interactions, icon: <Beaker className="w-4 h-4 text-indigo-600" /> },
    { title: 'Optimization Potential', value: data.optimization_potential, icon: <FlaskConical className="w-4 h-4 text-indigo-600" /> },
    { title: 'IUPAC Name', value: data.iupac_name, icon: <Dna className="w-4 h-4 text-indigo-600" /> },
  ].filter((section) => Boolean(section.value));

  useEffect(() => {
    const smiles = data.smiles?.trim();
    if (!isExpanded || !smiles || !structureCanvasRef.current) return;
    if (smiles.toLowerCase() === 'not publicly available') return;

    setSmilesError(null);
    try {
      const target = structureCanvasRef.current;
      const ctx = target.getContext('2d');
      if (!ctx) {
        setSmilesError('Canvas is not available to draw molecular diagram.');
        return;
      }
      ctx.clearRect(0, 0, target.width, target.height);

      const drawer = new (SmilesDrawer as any).Drawer({
        width: 640,
        height: 260,
        bondThickness: 1.2,
        shortBondLength: 0.8,
        compactDrawing: false,
      });
      const cleanedSmiles =
        typeof (SmilesDrawer as any).clean === 'function'
          ? (SmilesDrawer as any).clean(smiles)
          : smiles;

      (SmilesDrawer as any).parse(
        cleanedSmiles,
        (tree: any) => {
          drawer.draw(tree, target, 'light', false);
        },
        (err: any) => {
          const reason = err?.message ? ` (${err.message})` : '';
          setSmilesError(`Could not render molecular diagram for this SMILES${reason}.`);
        }
      );
    } catch {
      setSmilesError('Could not render molecular diagram for this SMILES.');
    }
  }, [data.smiles, isExpanded]);

  return (
    <div className="border border-blue-200 rounded-xl overflow-hidden bg-white shadow-sm">
      {/* Header */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white cursor-pointer hover:from-blue-700 hover:to-indigo-700 transition-colors"
      >
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Beaker className="w-6 h-6" />
            <div className="text-left">
              <h2 className="text-lg font-bold">{data.compound_name}</h2>
              <p className="text-blue-100 text-sm">Chemical Intelligence Snapshot</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div
              className={`px-3 py-1 rounded-full text-xs font-semibold border bg-white ${confidenceColor}`}
            >
              {data.evidence_confidence} confidence
            </div>
            {isExpanded ? (
              <ChevronUp className="w-6 h-6" />
            ) : (
              <ChevronDown className="w-6 h-6" />
            )}
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="p-5 space-y-5 bg-slate-50/40">
          {data.smiles && data.smiles.toLowerCase() !== 'not publicly available' && (
            <div className="rounded-xl border border-indigo-100 bg-gradient-to-br from-indigo-50 to-blue-50 p-4">
              <div className="flex items-center justify-between gap-3 mb-3">
                <p className="text-xs font-semibold text-indigo-700 uppercase tracking-wide">
                  2D Molecular Structure
                </p>
                <span className="text-[11px] font-mono text-indigo-700 bg-white/80 px-2 py-1 rounded border border-indigo-100 break-all">
                  {data.smiles}
                </span>
              </div>
              <div className="rounded-lg bg-white border border-indigo-100 p-2 min-h-[220px] flex items-center justify-center">
                {smilesError ? (
                  <p className="text-sm text-amber-700">{smilesError}</p>
                ) : (
                  <canvas ref={structureCanvasRef} width={640} height={260} className="w-full max-w-3xl h-[220px]" />
                )}
              </div>
            </div>
          )}

          {summaryCards.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {summaryCards.map((card) => (
                <div key={card.label} className="rounded-lg border border-blue-100 bg-white px-3 py-2">
                  <div className="flex items-center gap-2 text-xs text-slate-500 uppercase tracking-wide font-semibold">
                    {card.icon}
                    {card.label}
                  </div>
                  <p className="text-sm font-medium text-slate-900 mt-1 break-words">{card.value}</p>
                </div>
              ))}
            </div>
          )}

          {data.similar_drugs && data.similar_drugs.length > 0 && (
            <div className="rounded-lg border border-emerald-100 bg-emerald-50/60 p-3">
              <p className="text-xs font-semibold text-emerald-800 uppercase tracking-wide mb-2">
                Similar Approved Drugs
              </p>
              <div className="flex flex-wrap gap-2">
                {data.similar_drugs.map((drug, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-full text-xs font-medium bg-white border border-emerald-200 text-emerald-900"
                  >
                    {drug}
                  </span>
                ))}
              </div>
            </div>
          )}

          {data.safety_considerations && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
              <div className="flex items-center gap-2 mb-1">
                <ShieldAlert className="w-4 h-4 text-amber-700" />
                <p className="text-xs font-semibold text-amber-800 uppercase tracking-wide">
                  Safety Considerations
                </p>
              </div>
              <p className="text-sm text-amber-900 leading-relaxed whitespace-pre-wrap break-words">
                {data.safety_considerations}
              </p>
            </div>
          )}

          {data.allergy_medical_cautions && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3">
              <div className="flex items-center gap-2 mb-1">
                <AlertCircle className="w-4 h-4 text-rose-700" />
                <p className="text-xs font-semibold text-rose-800 uppercase tracking-wide">
                  Allergy & Medical Cautions
                </p>
              </div>
              <p className="text-sm text-rose-900 leading-relaxed whitespace-pre-wrap break-words">
                {data.allergy_medical_cautions}
              </p>

              {data.suggested_alternatives && data.suggested_alternatives.length > 0 && (
                <div className="mt-3">
                  <p className="text-[11px] font-semibold text-rose-700 uppercase tracking-wide mb-1">
                    Suggested Alternatives
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {data.suggested_alternatives.map((alt, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-full text-xs font-medium bg-white border border-rose-200 text-rose-900"
                      >
                        {alt}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {detailSections.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {detailSections.map((section) => (
                <div key={section.title} className="rounded-lg border border-slate-200 bg-white p-3">
                  <div className="flex items-center gap-2 mb-2">
                    {section.icon}
                    <p className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
                      {section.title}
                    </p>
                  </div>
                  <p className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap break-words">
                    {section.value}
                  </p>
                </div>
              ))}
            </div>
          )}

          <div className="px-1 text-xs text-slate-500 flex items-center justify-between">
            <span>Analyzed with Gemini</span>
            <span>{data.evidence_confidence} confidence</span>
          </div>
        </div>
      )}
    </div>
  );
};
