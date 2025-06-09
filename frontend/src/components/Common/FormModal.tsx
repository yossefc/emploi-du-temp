import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  XMarkIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  CloudArrowUpIcon,
  EyeIcon,
  PencilIcon,
  DocumentDuplicateIcon
} from '@heroicons/react/24/outline';
import { useForm } from '../../hooks/useForm';

export interface FormStep {
  key: string;
  title: string;
  description?: string;
  fields: string[];
  optional?: boolean;
  validation?: (values: any) => Record<string, string> | Promise<Record<string, string>>;
}

export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'textarea' | 'select' | 'checkbox' | 'radio' | 'date' | 'file' | 'custom';
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  options?: Array<{ label: string; value: any }>;
  validation?: (value: any, allValues: any) => string | Promise<string>;
  render?: (field: FormField, value: any, onChange: (value: any) => void, error?: string) => React.ReactNode;
  accept?: string; // For file inputs
  multiple?: boolean; // For file inputs
  rows?: number; // For textarea
  min?: number | string;
  max?: number | string;
  step?: number | string;
  pattern?: string;
  autoComplete?: string;
  dependencies?: string[]; // Fields this field depends on
}

export interface FormModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  mode: 'create' | 'edit' | 'view' | 'duplicate';
  fields: FormField[];
  steps?: FormStep[];
  initialValues?: Record<string, any>;
  onSubmit: (values: Record<string, any>, mode: string) => Promise<void>;
  onDraft?: (values: Record<string, any>) => void;
  loading?: boolean;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  showProgress?: boolean;
  confirmBeforeClose?: boolean;
  autoSave?: boolean;
  autoSaveInterval?: number; // in milliseconds
  className?: string;
  submitLabel?: string;
  cancelLabel?: string;
  resetLabel?: string;
  duplicateLabel?: string;
  editLabel?: string;
  allowModeSwitch?: boolean;
  customActions?: Array<{
    key: string;
    label: string;
    icon?: React.ReactNode;
    onClick: (values: Record<string, any>) => void;
    disabled?: boolean;
    type?: 'primary' | 'secondary' | 'danger';
  }>;
}

export default function FormModal({
  open,
  onClose,
  title,
  mode: initialMode,
  fields,
  steps,
  initialValues = {},
  onSubmit,
  onDraft,
  loading = false,
  size = 'md',
  showProgress = true,
  confirmBeforeClose = true,
  autoSave = false,
  autoSaveInterval = 30000,
  className = '',
  submitLabel,
  cancelLabel = 'Annuler',
  resetLabel = 'Réinitialiser',
  duplicateLabel = 'Dupliquer',
  editLabel = 'Modifier',
  allowModeSwitch = true,
  customActions = []
}: FormModalProps) {
  const [mode, setMode] = useState(initialMode);
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [showConfirmClose, setShowConfirmClose] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const autoSaveTimeoutRef = useRef<NodeJS.Timeout>();

  const {
    values,
    errors,
    touched,
    isDirty,
    isSubmitting,
    handleChange,
    handleBlur,
    handleSubmit,
    resetForm,
    setFieldValue,
    setFieldError,
    validateField,
    validateForm,
    setValues
  } = useForm({
    initialValues,
    fields,
    onSubmit: async (formValues) => {
      await onSubmit(formValues, mode);
      if (mode === 'create' || mode === 'duplicate') {
        resetForm();
      }
    }
  });

  // Update mode when prop changes
  useEffect(() => {
    setMode(initialMode);
  }, [initialMode]);

  // Update form values when initialValues change
  useEffect(() => {
    if (open) {
      setValues(initialValues);
      setCurrentStep(0);
      setCompletedSteps(new Set());
    }
  }, [open, initialValues, setValues]);

  // Auto-save functionality
  useEffect(() => {
    if (!autoSave || !onDraft || !isDirty || mode === 'view') return;

    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }

    autoSaveTimeoutRef.current = setTimeout(() => {
      onDraft(values);
    }, autoSaveInterval);

    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, [values, isDirty, autoSave, onDraft, autoSaveInterval, mode]);

  const isMultiStep = Boolean(steps && steps.length > 1);
  const isViewMode = mode === 'view';
  const canEdit = !isViewMode && !loading;

  const currentStepConfig = useMemo(() => {
    if (!isMultiStep || !steps) return null;
    return steps[currentStep];
  }, [isMultiStep, steps, currentStep]);

  const currentStepFields = useMemo(() => {
    if (!isMultiStep || !currentStepConfig) return fields;
    return fields.filter(field => currentStepConfig.fields.includes(field.name));
  }, [isMultiStep, currentStepConfig, fields]);

  const getModalSize = () => {
    const sizes = {
      sm: 'max-w-md',
      md: 'max-w-lg',
      lg: 'max-w-2xl',
      xl: 'max-w-4xl',
      full: 'max-w-full mx-4'
    };
    return sizes[size];
  };

  const handleClose = useCallback(() => {
    if (confirmBeforeClose && isDirty && !isViewMode) {
      setShowConfirmClose(true);
    } else {
      onClose();
    }
  }, [confirmBeforeClose, isDirty, isViewMode, onClose]);

  const handleConfirmClose = useCallback(() => {
    setShowConfirmClose(false);
    onClose();
  }, [onClose]);

  const handleModeSwitch = useCallback((newMode: 'create' | 'edit' | 'view' | 'duplicate') => {
    if (!allowModeSwitch) return;
    setMode(newMode);
    
    if (newMode === 'duplicate') {
      // Reset ID field for duplication
      const { id, ...duplicatedValues } = values;
      setValues(duplicatedValues);
    }
  }, [allowModeSwitch, values, setValues]);

  const validateCurrentStep = useCallback(async () => {
    if (!isMultiStep || !currentStepConfig) {
      return await validateForm();
    }

    const stepErrors: Record<string, string> = {};
    
    // Validate fields in current step
    for (const fieldName of currentStepConfig.fields) {
      const error = await validateField(fieldName, values[fieldName]);
      if (error) {
        stepErrors[fieldName] = error;
      }
    }

    // Custom step validation
    if (currentStepConfig.validation) {
      const customErrors = await currentStepConfig.validation(values);
      Object.assign(stepErrors, customErrors);
    }

    return Object.keys(stepErrors).length === 0;
  }, [isMultiStep, currentStepConfig, validateForm, validateField, values]);

  const handleNextStep = useCallback(async () => {
    if (!isMultiStep || !steps) return;

    const isValid = await validateCurrentStep();
    if (isValid) {
      setCompletedSteps(prev => new Set([...prev, currentStep]));
      if (currentStep < steps.length - 1) {
        setCurrentStep(currentStep + 1);
      }
    }
  }, [isMultiStep, steps, currentStep, validateCurrentStep]);

  const handlePrevStep = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  }, [currentStep]);

  const handleStepClick = useCallback((stepIndex: number) => {
    if (stepIndex <= currentStep || completedSteps.has(stepIndex)) {
      setCurrentStep(stepIndex);
    }
  }, [currentStep, completedSteps]);

  const handleFileUpload = useCallback(async (field: FormField, files: FileList | null) => {
    if (!files) return;

    const uploadPromises = Array.from(files).map(async (file, index) => {
      const formData = new FormData();
      formData.append('file', file);

      // Simulate upload progress
      setUploadProgress(prev => ({ ...prev, [`${field.name}_${index}`]: 0 }));

      try {
        // Replace with actual upload logic
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        setUploadProgress(prev => ({ ...prev, [`${field.name}_${index}`]: 100 }));
        
        return {
          name: file.name,
          size: file.size,
          type: file.type,
          url: URL.createObjectURL(file) // Replace with actual URL
        };
      } catch (error) {
        setFieldError(field.name, 'Erreur lors du téléchargement');
        throw error;
      }
    });

    try {
      const uploadedFiles = await Promise.all(uploadPromises);
      const newValue = field.multiple ? uploadedFiles : uploadedFiles[0];
      setFieldValue(field.name, newValue);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  }, [setFieldValue, setFieldError]);

  const renderField = useCallback((field: FormField) => {
    const value = values[field.name];
    const error = touched[field.name] ? errors[field.name] : '';
    const disabled = field.disabled || isViewMode || loading;

    const commonProps = {
      id: field.name,
      name: field.name,
      disabled,
      className: `
        w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400
        focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500
        ${error ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}
        ${disabled ? 'bg-gray-50 cursor-not-allowed' : ''}
      `,
      onChange: (e: any) => handleChange(field.name, e.target ? e.target.value : e),
      onBlur: () => handleBlur(field.name)
    };

    // Custom render function
    if (field.render) {
      return field.render(field, value, (newValue) => setFieldValue(field.name, newValue), error);
    }

    switch (field.type) {
      case 'textarea':
        return (
          <textarea
            {...commonProps}
            rows={field.rows || 3}
            placeholder={field.placeholder}
            value={value || ''}
          />
        );

      case 'select':
        return (
          <select {...commonProps} value={value || ''}>
            <option value="">{field.placeholder || 'Sélectionner...'}</option>
            {field.options?.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );

      case 'checkbox':
        return (
          <div className="flex items-center">
            <input
              type="checkbox"
              {...commonProps}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              checked={Boolean(value)}
              onChange={(e) => handleChange(field.name, e.target.checked)}
            />
            <label htmlFor={field.name} className="ml-2 block text-sm text-gray-900">
              {field.placeholder}
            </label>
          </div>
        );

      case 'radio':
        return (
          <div className="space-y-2">
            {field.options?.map(option => (
              <div key={option.value} className="flex items-center">
                <input
                  type="radio"
                  id={`${field.name}_${option.value}`}
                  name={field.name}
                  value={option.value}
                  checked={value === option.value}
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                  disabled={disabled}
                />
                <label htmlFor={`${field.name}_${option.value}`} className="ml-2 block text-sm text-gray-900">
                  {option.label}
                </label>
              </div>
            ))}
          </div>
        );

      case 'file':
        return (
          <div>
            <input
              type="file"
              {...commonProps}
              accept={field.accept}
              multiple={field.multiple}
              onChange={(e) => handleFileUpload(field, e.target.files)}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
            />
            
            {/* File preview */}
            {value && (
              <div className="mt-2 space-y-2">
                {(Array.isArray(value) ? value : [value]).map((file: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">{file.name}</span>
                    {uploadProgress[`${field.name}_${index}`] !== undefined && (
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${uploadProgress[`${field.name}_${index}`]}%` }}
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        );

      default:
        return (
          <input
            type={field.type}
            {...commonProps}
            placeholder={field.placeholder}
            value={value || ''}
            min={field.min}
            max={field.max}
            step={field.step}
            pattern={field.pattern}
            autoComplete={field.autoComplete}
          />
        );
    }
  }, [values, errors, touched, isViewMode, loading, handleChange, handleBlur, setFieldValue, handleFileUpload, uploadProgress]);

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity z-40" />
      
      {/* Modal */}
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          <div className={`
            relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all
            ${getModalSize()} w-full ${className}
          `}>
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <h3 className="text-lg font-medium text-gray-900">{title}</h3>
                
                {/* Mode badges */}
                <span className={`
                  inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                  ${mode === 'create' ? 'bg-green-100 text-green-800' :
                    mode === 'edit' ? 'bg-blue-100 text-blue-800' :
                    mode === 'view' ? 'bg-gray-100 text-gray-800' :
                    'bg-purple-100 text-purple-800'}
                `}>
                  {mode === 'create' ? 'Création' :
                   mode === 'edit' ? 'Modification' :
                   mode === 'view' ? 'Consultation' :
                   'Duplication'}
                </span>

                {/* Auto-save indicator */}
                {autoSave && isDirty && !isViewMode && (
                  <span className="inline-flex items-center px-2 py-1 rounded text-xs text-gray-500">
                    <div className="w-2 h-2 bg-orange-400 rounded-full mr-1 animate-pulse"></div>
                    Sauvegarde automatique...
                  </span>
                )}
              </div>

              <div className="flex items-center space-x-2">
                {/* Mode switch buttons */}
                {allowModeSwitch && (
                  <div className="flex items-center space-x-1">
                    {mode === 'view' && (
                      <button
                        onClick={() => handleModeSwitch('edit')}
                        className="inline-flex items-center px-2 py-1 text-xs text-gray-600 hover:text-gray-900"
                      >
                        <PencilIcon className="w-3 h-3 mr-1" />
                        {editLabel}
                      </button>
                    )}
                    
                    {(mode === 'view' || mode === 'edit') && (
                      <button
                        onClick={() => handleModeSwitch('duplicate')}
                        className="inline-flex items-center px-2 py-1 text-xs text-gray-600 hover:text-gray-900"
                      >
                        <DocumentDuplicateIcon className="w-3 h-3 mr-1" />
                        {duplicateLabel}
                      </button>
                    )}
                  </div>
                )}

                <button
                  onClick={handleClose}
                  className="text-gray-400 hover:text-gray-600 focus:outline-none"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Progress Steps */}
            {isMultiStep && showProgress && steps && (
              <div className="px-6 py-4 border-b border-gray-200">
                <nav aria-label="Progress">
                  <ol className="flex items-center">
                    {steps.map((step, index) => (
                      <li key={step.key} className="relative flex-1">
                        {index !== 0 && (
                          <div className="absolute inset-0 flex items-center" aria-hidden="true">
                            <div className="h-0.5 w-full bg-gray-200" />
                          </div>
                        )}
                        
                        <button
                          onClick={() => handleStepClick(index)}
                          className={`
                            relative flex h-8 w-8 items-center justify-center rounded-full border-2 text-sm font-medium
                            ${index === currentStep
                              ? 'border-indigo-600 bg-indigo-600 text-white'
                              : completedSteps.has(index)
                              ? 'border-indigo-600 bg-indigo-600 text-white'
                              : index < currentStep
                              ? 'border-gray-300 bg-white text-gray-500 hover:border-gray-400'
                              : 'border-gray-300 bg-white text-gray-500'
                            }
                          `}
                          disabled={index > currentStep && !completedSteps.has(index)}
                        >
                          {completedSteps.has(index) ? (
                            <CheckIcon className="w-4 h-4" />
                          ) : (
                            <span>{index + 1}</span>
                          )}
                        </button>
                        
                        <div className="mt-2">
                          <p className="text-xs font-medium text-gray-900">{step.title}</p>
                          {step.description && (
                            <p className="text-xs text-gray-500">{step.description}</p>
                          )}
                        </div>
                      </li>
                    ))}
                  </ol>
                </nav>
              </div>
            )}

            {/* Form Content */}
            <form onSubmit={handleSubmit} className="flex-1">
              <div className="px-6 py-6 space-y-6 max-h-96 overflow-y-auto">
                {currentStepFields.map(field => (
                  <div key={field.name}>
                    <label htmlFor={field.name} className="block text-sm font-medium text-gray-700 mb-1">
                      {field.label}
                      {field.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    
                    {renderField(field)}
                    
                    {touched[field.name] && errors[field.name] && (
                      <p className="mt-1 text-sm text-red-600">{errors[field.name]}</p>
                    )}
                  </div>
                ))}
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {/* Step navigation */}
                  {isMultiStep && (
                    <>
                      <button
                        type="button"
                        onClick={handlePrevStep}
                        disabled={currentStep === 0}
                        className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <ArrowLeftIcon className="w-4 h-4 mr-1" />
                        Précédent
                      </button>
                      
                      {currentStep < steps!.length - 1 ? (
                        <button
                          type="button"
                          onClick={handleNextStep}
                          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                          Suivant
                          <ArrowRightIcon className="w-4 h-4 ml-1" />
                        </button>
                      ) : null}
                    </>
                  )}

                  {/* Custom actions */}
                  {customActions.map(action => (
                    <button
                      key={action.key}
                      type="button"
                      onClick={() => action.onClick(values)}
                      disabled={action.disabled || loading}
                      className={`
                        inline-flex items-center px-3 py-2 border text-sm leading-4 font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2
                        ${action.type === 'danger'
                          ? 'border-red-300 text-red-700 bg-red-50 hover:bg-red-100 focus:ring-red-500'
                          : action.type === 'primary'
                          ? 'border-transparent text-white bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500'
                          : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50 focus:ring-indigo-500'
                        }
                        disabled:opacity-50 disabled:cursor-not-allowed
                      `}
                    >
                      {action.icon && <span className="mr-1">{action.icon}</span>}
                      {action.label}
                    </button>
                  ))}
                </div>

                <div className="flex items-center space-x-3">
                  {/* Reset button */}
                  {!isViewMode && isDirty && (
                    <button
                      type="button"
                      onClick={resetForm}
                      className="text-sm text-gray-600 hover:text-gray-900"
                    >
                      {resetLabel}
                    </button>
                  )}

                  {/* Cancel button */}
                  <button
                    type="button"
                    onClick={handleClose}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    {cancelLabel}
                  </button>

                  {/* Submit button */}
                  {!isViewMode && (
                    <button
                      type="submit"
                      disabled={loading || isSubmitting || (isMultiStep && currentStep < steps!.length - 1)}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {(loading || isSubmitting) && (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      )}
                      {submitLabel || (mode === 'create' ? 'Créer' : mode === 'edit' ? 'Modifier' : 'Dupliquer')}
                    </button>
                  )}
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* Confirm Close Dialog */}
      {showConfirmClose && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity z-60">
          <div className="fixed inset-0 z-60 overflow-y-auto">
            <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
              <div className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="sm:flex sm:items-start">
                    <div className="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-yellow-100 sm:mx-0 sm:h-10 sm:w-10">
                      <ExclamationTriangleIcon className="h-6 w-6 text-yellow-600" aria-hidden="true" />
                    </div>
                    <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                      <h3 className="text-lg font-medium leading-6 text-gray-900">
                        Modifications non sauvegardées
                      </h3>
                      <div className="mt-2">
                        <p className="text-sm text-gray-500">
                          Vous avez des modifications non sauvegardées. Êtes-vous sûr de vouloir fermer sans sauvegarder ?
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                  <button
                    type="button"
                    onClick={handleConfirmClose}
                    className="inline-flex w-full justify-center rounded-md border border-transparent bg-red-600 px-4 py-2 text-base font-medium text-white shadow-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 sm:ml-3 sm:w-auto sm:text-sm"
                  >
                    Fermer sans sauvegarder
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowConfirmClose(false)}
                    className="mt-3 inline-flex w-full justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-base font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                  >
                    Continuer l'édition
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}