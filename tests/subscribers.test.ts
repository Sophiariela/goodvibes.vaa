import { describe, it, expect } from 'vitest';
import { isValidEmail } from '../lib/subscribers';

describe('isValidEmail', () => {
  it('accepts common real-world addresses', () => {
    expect(isValidEmail('ana@gmail.com')).toBe(true);
    expect(isValidEmail('ana.silva+teste@good-vibes.com.br')).toBe(true);
    expect(isValidEmail('  ana@gmail.com  ')).toBe(true);
  });

  it('rejects malformed input', () => {
    expect(isValidEmail('')).toBe(false);
    expect(isValidEmail('ana@')).toBe(false);
    expect(isValidEmail('@gmail.com')).toBe(false);
    expect(isValidEmail('ana gmail.com')).toBe(false);
    expect(isValidEmail('ana@gmail')).toBe(false);
    expect(isValidEmail(123 as unknown as string)).toBe(false);
    expect(isValidEmail(null as unknown as string)).toBe(false);
  });

  it('rejects absurdly long input', () => {
    const long = `${'a'.repeat(260)}@gmail.com`;
    expect(isValidEmail(long)).toBe(false);
  });
});
