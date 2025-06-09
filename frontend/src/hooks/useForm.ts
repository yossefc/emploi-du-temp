import { useState, useCallback, useEffect } from 'react';
import { FormField } from '../components/Common/FormModal';

export interface UseFormOptions {
  initialValues: Record<string, any>;
  fields: FormField[];
  onSubmit: (values: Record<string, any>) => Promise<void>;
  validationMode?: 'onChange' | 'onBlur' | 'onSubmit';
  revalidateMode?: 'onChange' | 'onBlur';
}

export function useForm({
  initialValues,
  fields,
  onSubmit,
  validationMode = 'onBlur',
  revalidateMode = 'onChange'
}: UseFormOptions) {
  const [values, setValues] = useState<Record<string, any>>(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  // Check if form is dirty
  useEffect(() => {
    const isFormDirty = Object.keys(values).some(key => 
      values[key] !== initialValues[key]
    );
    setIsDirty(isFormDirty);
  }, [values, initialValues]);

  // Validate a single field
  const validateField = useCallback(async (name: string, value: any): Promise<string> => {
    const field = fields.find(f => f.name === name);
    if (!field) return '';

    // Required validation
    if (field.required) {
      if (value === null || value === undefined || value === '') {
        return `${field.label} est requis`;
      }
      
      // Special handling for arrays (file uploads, multi-select)
      if (Array.isArray(value) && value.length === 0) {
        return `${field.label} est requis`;
      }
    }

    // Type-specific validation
    switch (field.type) {
      case 'email':
        if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          return 'Format d\'email invalide';
        }
        break;

      case 'number':
        if (value !== '' && isNaN(Number(value))) {
          return 'Doit être un nombre valide';
        }
        if (field.min !== undefined && Number(value) < Number(field.min)) {
          return `Doit être supérieur ou égal à ${field.min}`;
        }
        if (field.max !== undefined && Number(value) > Number(field.max)) {
          return `Doit être inférieur ou égal à ${field.max}`;
        }
        break;

      case 'password':
        if (value && value.length < 6) {
          return 'Le mot de passe doit contenir au moins 6 caractères';
        }
        break;

      case 'text':
      case 'textarea':
        if (field.min && value && value.length < Number(field.min)) {
          return `Doit contenir au moins ${field.min} caractères`;
        }
        if (field.max && value && value.length > Number(field.max)) {
          return `Doit contenir au maximum ${field.max} caractères`;
        }
        if (field.pattern && value && !new RegExp(field.pattern).test(value)) {
          return 'Format invalide';
        }
        break;

      case 'date':
        if (value && isNaN(Date.parse(value))) {
          return 'Date invalide';
        }
        break;

      case 'file':
        if (value) {
          const files = Array.isArray(value) ? value : [value];
          const allowedTypes = field.accept?.split(',').map(type => type.trim()) || [];
          
          if (allowedTypes.length > 0) {
            for (const file of files) {
              if (file.type && !allowedTypes.some(type => 
                type === file.type || 
                (type.endsWith('/*') && file.type.startsWith(type.slice(0, -2)))
              )) {
                return `Type de fichier non autorisé. Types acceptés: ${field.accept}`;
              }
            }
          }
        }
        break;
    }

    // Custom field validation
    if (field.validation) {
      try {
        const customError = await field.validation(value, values);
        if (customError) return customError;
      } catch (error) {
        return 'Erreur de validation';
      }
    }

    // Dependency validation
    if (field.dependencies) {
      for (const depName of field.dependencies) {
        const depField = fields.find(f => f.name === depName);
        const depValue = values[depName];
        
        if (depField?.required && (!depValue || depValue === '')) {
          return `${depField.label} doit être renseigné en premier`;
        }
      }
    }

    return '';
  }, [fields, values]);

  // Validate all fields
  const validateForm = useCallback(async (): Promise<boolean> => {
    const newErrors: Record<string, string> = {};
    
    for (const field of fields) {
      const error = await validateField(field.name, values[field.name]);
      if (error) {
        newErrors[field.name] = error;
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [fields, values, validateField]);

  // Handle field change
  const handleChange = useCallback(async (name: string, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }));
    
    // Validate on change if configured
    if (validationMode === 'onChange' || (touched[name] && revalidateMode === 'onChange')) {
      const error = await validateField(name, value);
      setErrors(prev => ({ ...prev, [name]: error }));
    }
  }, [validationMode, revalidateMode, touched, validateField]);

  // Handle field blur
  const handleBlur = useCallback(async (name: string) => {
    setTouched(prev => ({ ...prev, [name]: true }));
    
    // Validate on blur if configured
    if (validationMode === 'onBlur') {
      const error = await validateField(name, values[name]);
      setErrors(prev => ({ ...prev, [name]: error }));
    }
  }, [validationMode, validateField, values]);

  // Handle form submission
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Mark all fields as touched
    const newTouched: Record<string, boolean> = {};
    fields.forEach(field => {
      newTouched[field.name] = true;
    });
    setTouched(newTouched);
    
    // Validate form
    const isValid = await validateForm();
    
    if (!isValid) {
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      await onSubmit(values);
    } catch (error) {
      console.error('Form submission error:', error);
      // Handle submission error - could set form-level error here
    } finally {
      setIsSubmitting(false);
    }
  }, [fields, validateForm, onSubmit, values]);

  // Set field value
  const setFieldValue = useCallback((name: string, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }));
  }, []);

  // Set field error
  const setFieldError = useCallback((name: string, error: string) => {
    setErrors(prev => ({ ...prev, [name]: error }));
  }, []);

  // Reset form
  const resetForm = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setIsDirty(false);
    setIsSubmitting(false);
  }, [initialValues]);

  // Get field props (helper for easier field binding)
  const getFieldProps = useCallback((name: string) => {
    const field = fields.find(f => f.name === name);
    return {
      name,
      value: values[name] || '',
      error: touched[name] ? errors[name] : '',
      onChange: (value: any) => handleChange(name, value),
      onBlur: () => handleBlur(name),
      required: field?.required,
      disabled: field?.disabled
    };
  }, [fields, values, errors, touched, handleChange, handleBlur]);

  // Check if field has error
  const hasFieldError = useCallback((name: string): boolean => {
    return Boolean(touched[name] && errors[name]);
  }, [touched, errors]);

  // Get field error
  const getFieldError = useCallback((name: string): string => {
    return touched[name] ? errors[name] || '' : '';
  }, [touched, errors]);

  return {
    values,
    errors,
    touched,
    isDirty,
    isSubmitting,
    handleChange,
    handleBlur,
    handleSubmit,
    setFieldValue,
    setFieldError,
    validateField,
    validateForm,
    resetForm,
    setValues,
    getFieldProps,
    hasFieldError,
    getFieldError
  };
}