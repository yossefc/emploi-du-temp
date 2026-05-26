import clsx from "clsx";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export interface WizardStep {
  id: string;
  label: string;
}

interface Props {
  steps: WizardStep[];
  currentIndex: number;
  onPrev?: () => void;
  onNext?: () => void;
  nextLabel?: string;
  nextDisabled?: boolean;
  nextLoading?: boolean;
  children: React.ReactNode;
  title: string;
  subtitle?: string;
}

export function WizardLayout({
  steps,
  currentIndex,
  onPrev,
  onNext,
  nextLabel = "Suivant",
  nextDisabled,
  nextLoading,
  children,
  title,
  subtitle,
}: Props) {
  return (
    <div className="space-y-6">
      {/* Indicateur d'étape */}
      <div className="flex flex-wrap items-center gap-2">
        {steps.map((step, i) => (
          <div key={step.id} className="flex items-center gap-2">
            <div
              className={clsx(
                "flex h-8 w-8 items-center justify-center rounded-full border text-sm font-medium",
                i < currentIndex && "bg-primary-600 text-white border-primary-600",
                i === currentIndex &&
                  "border-primary-600 text-primary-700 dark:text-primary-300 bg-primary-50 dark:bg-primary-900/30",
                i > currentIndex &&
                  "border-slate-300 dark:border-slate-600 text-slate-400 dark:text-slate-500"
              )}
            >
              {i < currentIndex ? "✓" : i + 1}
            </div>
            <span
              className={clsx(
                "hidden sm:inline text-sm",
                i === currentIndex
                  ? "text-slate-900 dark:text-slate-100 font-medium"
                  : "text-slate-500 dark:text-slate-400"
              )}
            >
              {step.label}
            </span>
            {i < steps.length - 1 && (
              <span className="text-slate-300 dark:text-slate-600">→</span>
            )}
          </div>
        ))}
      </div>

      <Card>
        <div className="p-4 sm:p-6 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
          {subtitle && (
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{subtitle}</p>
          )}
        </div>
        <div className="p-4 sm:p-6">{children}</div>
        <div className="p-4 sm:p-6 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 flex items-center justify-between gap-2">
          <Button
            variant="secondary"
            onClick={onPrev}
            disabled={!onPrev || currentIndex === 0}
          >
            ← Retour
          </Button>
          <Button onClick={onNext} disabled={nextDisabled} loading={nextLoading}>
            {nextLabel}
          </Button>
        </div>
      </Card>
    </div>
  );
}
