export const validateEmail = (email) => {
  if (!email) return { isValid: false, error: 'Email is required' };

  // Trim whitespace
  email = email.trim();

  // Basic length checks
  if (email.length > 255) {
    return { isValid: false, error: 'Email must not exceed 255 characters' };
  }
  if (email.length < 3) {
    return { isValid: false, error: 'Email is too short' };
  }

  const [localPart, domain] = email.split('@');

  // Local part validations
  if (localPart.length > 64) {
    return {
      isValid: false,
      error: 'Local part of email cannot exceed 64 characters',
    };
  }

  // Check for consecutive dots
  if (email.includes('..')) {
    return { isValid: false, error: 'Email cannot contain consecutive dots' };
  }

  // Check for starting/ending dots
  if (email.startsWith('.') || email.endsWith('.')) {
    return { isValid: false, error: 'Email cannot start or end with a dot' };
  }

  const hasAtSymbol = email.includes('@');
  const hasValidDomain = email.includes('.') && email.split('@')[1]?.includes('.');
  const hasNoSpaces = !/\s/.test(email);
  const hasValidChars = /^[\w%+.-]+@[\d.A-Za-z-]+\.[A-Za-z]{2,}$/.test(email);

  if (!hasAtSymbol) {
    return { isValid: false, error: 'Email must contain @ symbol' };
  }

  if (!hasValidDomain) {
    return {
      isValid: false,
      error: 'Email must have a valid domain (e.g., example.com)',
    };
  }

  if (!hasNoSpaces) {
    return { isValid: false, error: 'Email cannot contain spaces' };
  }

  if (!hasValidChars) {
    return { isValid: false, error: 'Email contains invalid characters' };
  }

  // Domain specific checks
  if (domain) {
    if (domain.length > 255) {
      return {
        isValid: false,
        error: 'Domain part cannot exceed 255 characters',
      };
    }

    const tld = domain.split('.').pop();
    if (tld && tld.length < 2) {
      return {
        isValid: false,
        error: 'Domain must have a valid top-level domain',
      };
    }
  }

  return { isValid: true, error: null };
};
