import { describe, it, expect } from 'vitest';
import {
  isValidEmail,
  isValidSubject,
  CONTACT_SUBJECTS,
  saveContactMessage,
  ContactError,
  NAME_MAX,
  MESSAGE_MAX,
} from '../lib/contact';

/** Entrada válida mínima — cada teste muda só o campo que está exercitando. */
const base = {
  name: 'Ana Silva',
  email: 'ana@gmail.com',
  subject: 'reserva',
  message: 'Gostaria de saber como funciona a primeira remada.',
  locale: 'pt' as const,
};

/** Sem SUPABASE_DB_URL, `query` lança DbNotConfiguredError. Isso é útil:
 *  se a validação passou, o erro que chega é o do banco — ou seja, a
 *  mensagem seria gravada. Se a validação barrou, vem ContactError. */
async function failureOf(input: Parameters<typeof saveContactMessage>[0]): Promise<Error> {
  try {
    await saveContactMessage(input);
    throw new Error('não deveria ter passado');
  } catch (err) {
    return err as Error;
  }
}

describe('isValidEmail', () => {
  it('aceita endereços reais e rejeita o óbvio errado', () => {
    expect(isValidEmail('ana@gmail.com')).toBe(true);
    expect(isValidEmail('  ana.silva+vaa@good-vibes.com.br  ')).toBe(true);
    expect(isValidEmail('ana@gmail')).toBe(false);
    expect(isValidEmail('')).toBe(false);
    expect(isValidEmail(null as unknown as string)).toBe(false);
  });
});

describe('isValidSubject', () => {
  it('aceita só os assuntos do formulário', () => {
    for (const s of CONTACT_SUBJECTS) expect(isValidSubject(s)).toBe(true);
    expect(isValidSubject('qualquer-coisa')).toBe(false);
    expect(isValidSubject('')).toBe(false);
    expect(isValidSubject(undefined)).toBe(false);
  });
});

describe('saveContactMessage — validação', () => {
  it('exige nome com pelo menos dois caracteres', async () => {
    const err = await failureOf({ ...base, name: ' A ' });
    expect(err).toBeInstanceOf(ContactError);
    expect((err as ContactError).code).toBe('INVALID_NAME');
  });

  it('recusa nome absurdamente longo', async () => {
    const err = await failureOf({ ...base, name: 'a'.repeat(NAME_MAX + 1) });
    expect((err as ContactError).code).toBe('INVALID_NAME');
  });

  it('recusa e-mail malformado', async () => {
    const err = await failureOf({ ...base, email: 'ana@' });
    expect((err as ContactError).code).toBe('INVALID_EMAIL');
  });

  it('recusa assunto fora da lista', async () => {
    const err = await failureOf({ ...base, subject: 'parceria' });
    expect((err as ContactError).code).toBe('INVALID_SUBJECT');
  });

  it('recusa mensagem curta demais ou longa demais', async () => {
    expect(((await failureOf({ ...base, message: 'oi' })) as ContactError).code).toBe('INVALID_MESSAGE');
    expect(((await failureOf({ ...base, message: 'a'.repeat(MESSAGE_MAX + 1) })) as ContactError).code).toBe('INVALID_MESSAGE');
  });

  it('com entrada válida chega até o banco (não barra na validação)', async () => {
    const err = await failureOf(base);
    expect(err).not.toBeInstanceOf(ContactError);
    expect(err.name).toBe('DbNotConfiguredError');
  });

  it('espaços em volta não derrubam uma entrada válida', async () => {
    const err = await failureOf({ ...base, name: '  Ana Silva  ', email: '  ana@gmail.com  ' });
    expect(err.name).toBe('DbNotConfiguredError');
  });
});
