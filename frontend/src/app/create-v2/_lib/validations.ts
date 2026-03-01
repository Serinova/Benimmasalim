import {
  MIN_NAME_LENGTH,
  MAX_NAME_LENGTH,
  MAX_DEDICATION_LENGTH,
} from "./constants";

export interface ValidationResult {
  valid: boolean;
  message: string;
}

const OK: ValidationResult = { valid: true, message: "" };

export function validateChildName(name: string): ValidationResult {
  const trimmed = name.trim();
  if (!trimmed) return { valid: false, message: "İsim zorunludur" };
  if (trimmed.length < MIN_NAME_LENGTH)
    return { valid: false, message: `En az ${MIN_NAME_LENGTH} karakter gerekli` };
  if (trimmed.length > MAX_NAME_LENGTH)
    return { valid: false, message: `En fazla ${MAX_NAME_LENGTH} karakter olabilir` };
  return OK;
}

export function validateAge(age: string): ValidationResult {
  if (!age) return { valid: false, message: "Yaş seçimi zorunludur" };
  const n = parseInt(age, 10);
  if (isNaN(n) || n < 3 || n > 12)
    return { valid: false, message: "3-12 yaş aralığında olmalı" };
  return OK;
}

export function validateGender(gender: string): ValidationResult {
  if (!gender) return { valid: false, message: "Cinsiyet seçimi zorunludur" };
  return OK;
}

export function validateScenario(scenarioId: string): ValidationResult {
  if (!scenarioId) return { valid: false, message: "Lütfen bir macera seçin" };
  return OK;
}

export function validateEmail(email: string): ValidationResult {
  if (!email.trim()) return { valid: false, message: "E-posta zorunludur" };
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!re.test(email.trim()))
    return { valid: false, message: "Geçerli bir e-posta adresi girin" };
  return OK;
}

export function validatePhone(phone: string): ValidationResult {
  const digits = phone.replace(/\D/g, "");
  if (!digits) return { valid: false, message: "Telefon zorunludur" };
  if (digits.length < 10)
    return { valid: false, message: "En az 10 haneli telefon numarası girin" };
  return OK;
}

export function validateFullName(name: string): ValidationResult {
  const trimmed = name.trim();
  if (!trimmed) return { valid: false, message: "Ad soyad zorunludur" };
  if (trimmed.length < 2)
    return { valid: false, message: "En az 2 karakter gerekli" };
  return OK;
}

export function validateAddress(address: string): ValidationResult {
  const trimmed = address.trim();
  if (!trimmed) return { valid: false, message: "Adres zorunludur" };
  if (trimmed.length < 5)
    return { valid: false, message: "Lütfen geçerli bir adres girin" };
  return OK;
}

export function validateCity(city: string): ValidationResult {
  if (!city.trim()) return { valid: false, message: "Şehir zorunludur" };
  return OK;
}

export function validateDedication(note: string): ValidationResult {
  if (note.length > MAX_DEDICATION_LENGTH)
    return { valid: false, message: `En fazla ${MAX_DEDICATION_LENGTH} karakter` };
  return OK;
}

export function validateTaxId(taxId: string): ValidationResult {
  if (!taxId.trim()) return { valid: false, message: "Vergi numarası zorunludur" };
  if (!/^\d{10,11}$/.test(taxId.trim()))
    return { valid: false, message: "10 veya 11 haneli vergi numarası girin" };
  return OK;
}

export function validateTcNo(tcNo: string): ValidationResult {
  if (!tcNo.trim()) return OK; // opsiyonel
  if (!/^\d{11}$/.test(tcNo.trim()))
    return { valid: false, message: "TC kimlik numarası 11 haneli rakamdan oluşmalıdır" };
  return OK;
}

export function validateCompanyName(name: string): ValidationResult {
  if (!name.trim()) return { valid: false, message: "Şirket ünvanı zorunludur" };
  return OK;
}

export function validateStep1(data: {
  childName: string;
  childAge: string;
  childGender: string;
  scenarioId: string;
}): boolean {
  return (
    validateChildName(data.childName).valid &&
    validateAge(data.childAge).valid &&
    validateGender(data.childGender).valid &&
    validateScenario(data.scenarioId).valid
  );
}

export function validateStep2(data: {
  faceDetected: boolean;
  selectedStyle: string;
  kvkkConsent: boolean;
}): boolean {
  return data.faceDetected && !!data.selectedStyle && data.kvkkConsent;
}

export function validateStep4Shipping(data: {
  fullName: string;
  email: string;
  phone: string;
  address: string;
  city: string;
}): boolean {
  return (
    validateFullName(data.fullName).valid &&
    validateEmail(data.email).valid &&
    validatePhone(data.phone).valid &&
    validateAddress(data.address).valid &&
    validateCity(data.city).valid
  );
}
