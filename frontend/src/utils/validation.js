import * as yup from 'yup';

// Regular expression to validate allowed characters in the email
const emailRegex = /^[\w%+.-]+@[\d.A-Za-z-]+\.[A-Za-z]{2,}$/;

// Only use when email is a required field
const emailSchema = yup
  .string()
  .trim('Email cannot contain leading or trailing spaces')
  .strict(true) // Ensures that trimmed value is used
  .required('Email is required')
  .min(3, 'Email is too short')
  .max(255, 'Email must not exceed 255 characters')
  .email('Invalid email format')
  .matches(emailRegex, 'Email contains invalid characters');

const optinalEmailSchema = yup
  .string()
  .trim('Email cannot contain leading or trailing spaces')
  .strict(true) // Ensures that trimmed value is used
  .max(255, 'Email must not exceed 255 characters')
  .email('Invalid email format')
  .matches(emailRegex, 'Email contains invalid characters');

// Only use when password is a required field
const passwordSchema = yup
  .string()
  .min(8, 'Password must be at least 8 characters long')
  .matches(/\d/, 'Password requires a number')
  .matches(/[a-z]/, 'Password requires a lowercase letter')
  .matches(/[A-Z]/, 'Password requires an uppercase letter')
  .matches(/\W/, 'Password requires a symbol')
  .max(40, 'Password must not exceed 40 characters')
  .required('Password is required');

const confirmPasswordSchema = yup
  .string('Confirm your password')
  .oneOf([yup.ref('password'), null], 'Passwords must match')
  .required('Confirm Password is required');

const confirmNewPasswordSchema = yup
  .string('Confirm your password')
  .oneOf([yup.ref('newPassword'), null], 'Passwords must match')
  .required('Confirm Password is required');

const firstNameSchema = yup
  .string()
  .trim()
  .max(100, 'First name must not exceed 100 characters')
  .required('First name is required');

const lastNameSchema = yup
  .string()
  .trim()
  .max(100, 'Last name must not exceed 100 characters')
  .required('Last name is required');

export {
  emailSchema,
  optinalEmailSchema,
  passwordSchema,
  firstNameSchema,
  lastNameSchema,
  confirmPasswordSchema,
  confirmNewPasswordSchema,
};
