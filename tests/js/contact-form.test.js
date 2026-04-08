/**
 * Feature: arpilf-website-rebuild, Property 8: Validação client-side do formulário de contacto
 *
 * Para qualquer input no formulário de contacto, a validação JavaScript client-side
 * deve identificar corretamente: emails com formato inválido (sem @, sem domínio, etc.)
 * e campos obrigatórios vazios, impedindo a submissão e mostrando mensagens de erro
 * em português junto a cada campo.
 *
 * **Validates: Requirements 5.6**
 */
import { describe, it, expect, beforeEach } from 'vitest';
import * as fc from 'fast-check';

// --- DOM setup helper ---

/**
 * Creates the minimal DOM structure that contact-form.js expects:
 * input fields with ids + corresponding error <p> elements.
 */
function setupDOM() {
  document.body.innerHTML = `
    <form id="contact-form" novalidate>
      <input type="text" id="nome" value="" />
      <p id="nome-error" class="hidden"></p>

      <input type="email" id="email" value="" />
      <p id="email-error" class="hidden"></p>

      <input type="text" id="assunto" value="" />
      <p id="assunto-error" class="hidden"></p>

      <textarea id="mensagem"></textarea>
      <p id="mensagem-error" class="hidden"></p>

      <input type="checkbox" id="consentimento" />
      <p id="consentimento-error" class="hidden"></p>
    </form>
  `;
}

// --- Load the module under test ---
let contactForm;

function loadModule() {
  const modulePath = require.resolve('../../static/js/contact-form.js');
  delete require.cache[modulePath];
  contactForm = require('../../static/js/contact-form.js');
}

// --- Helpers ---

function setFieldValue(id, value) {
  const el = document.getElementById(id);
  if (el) el.value = value;
}

function setCheckbox(id, checked) {
  const el = document.getElementById(id);
  if (el) el.checked = checked;
}

function getErrorText(fieldId) {
  const el = document.getElementById(fieldId + '-error');
  return el ? el.textContent : '';
}

function isErrorVisible(fieldId) {
  const el = document.getElementById(fieldId + '-error');
  return el ? !el.classList.contains('hidden') : false;
}

// --- Generators (fast-check v4 compatible — no fc.char() or fc.stringOf()) ---

/**
 * Generates strings that are definitely NOT valid emails per /^[^\s@]+@[^\s@]+\.[^\s@]+$/
 */
const invalidEmailArb = fc.oneof(
  // Strings without '@' at all (alphanumeric only, guaranteed no @)
  fc.stringMatching(/^[a-zA-Z0-9._]{1,30}$/),
  // Has '@' but nothing after it
  fc.stringMatching(/^[a-zA-Z0-9._]{1,15}$/).map((s) => s + '@'),
  // Has '@' but no dot in domain part
  fc.tuple(
    fc.stringMatching(/^[a-zA-Z0-9]{1,10}$/),
    fc.stringMatching(/^[a-zA-Z0-9]{1,10}$/)
  ).map(([local, domain]) => `${local}@${domain}`),
  // Contains whitespace (always invalid)
  fc.tuple(
    fc.stringMatching(/^[a-zA-Z]{1,8}$/),
    fc.stringMatching(/^[a-zA-Z]{1,8}$/)
  ).map(([a, b]) => `${a} ${b}@example.com`),
  // Empty string
  fc.constant('')
);

/**
 * Generates strings that are valid emails per the regex /^[^\s@]+@[^\s@]+\.[^\s@]+$/
 */
const validEmailArb = fc.tuple(
  fc.stringMatching(/^[a-zA-Z0-9._]{1,12}$/),
  fc.stringMatching(/^[a-zA-Z0-9]{1,8}$/),
  fc.stringMatching(/^[a-zA-Z]{2,5}$/)
).map(([local, domain, tld]) => `${local}@${domain}.${tld}`);

/**
 * Generates non-empty trimmed strings (valid required field values).
 */
const nonEmptyStringArb = fc.stringMatching(/^[a-zA-Z0-9 áéíóúàãõçÁÉÍÓÚÀÃÕÇ]{1,50}$/)
  .filter((s) => s.trim().length > 0);

/**
 * Generates empty or whitespace-only strings (invalid required field values).
 */
const emptyOrWhitespaceArb = fc.oneof(
  fc.constant(''),
  fc.constant(' '),
  fc.constant('  '),
  fc.constant('\t'),
  fc.constant('\n'),
  fc.constant('   \t  ')
);

// --- Property-based tests ---

describe('Property 8: Validação client-side do formulário de contacto', () => {
  beforeEach(() => {
    setupDOM();
    loadModule();
  });

  it('rejects invalid email formats and shows pt-PT error message', () => {
    fc.assert(
      fc.property(invalidEmailArb, (email) => {
        setupDOM();
        loadModule();

        setFieldValue('email', email);
        const result = contactForm.validateEmail();

        // Invalid emails must be rejected
        expect(result).toBe(false);

        // Error message must be visible and in pt-PT
        expect(isErrorVisible('email')).toBe(true);
        const errorText = getErrorText('email');
        expect(
          errorText === contactForm.MESSAGES.required ||
          errorText === contactForm.MESSAGES.email
        ).toBe(true);
      }),
      { numRuns: 10 }
    );
  });

  it('accepts valid email formats', () => {
    fc.assert(
      fc.property(validEmailArb, (email) => {
        setupDOM();
        loadModule();

        setFieldValue('email', email);
        const result = contactForm.validateEmail();

        expect(result).toBe(true);
        expect(isErrorVisible('email')).toBe(false);
      }),
      { numRuns: 10 }
    );
  });

  it('rejects empty/whitespace required fields and shows pt-PT error', () => {
    const requiredTextFields = ['nome', 'assunto', 'mensagem'];

    fc.assert(
      fc.property(
        fc.constantFrom(...requiredTextFields),
        emptyOrWhitespaceArb,
        (fieldId, value) => {
          setupDOM();
          loadModule();

          setFieldValue(fieldId, value);
          const result = contactForm.validateRequired(fieldId);

          expect(result).toBe(false);
          expect(isErrorVisible(fieldId)).toBe(true);
          expect(getErrorText(fieldId)).toBe(contactForm.MESSAGES.required);
        }
      ),
      { numRuns: 10 }
    );
  });

  it('accepts non-empty required fields', () => {
    const requiredTextFields = ['nome', 'assunto', 'mensagem'];

    fc.assert(
      fc.property(
        fc.constantFrom(...requiredTextFields),
        nonEmptyStringArb,
        (fieldId, value) => {
          setupDOM();
          loadModule();

          setFieldValue(fieldId, value);
          const result = contactForm.validateRequired(fieldId);

          expect(result).toBe(true);
          expect(isErrorVisible(fieldId)).toBe(false);
        }
      ),
      { numRuns: 10 }
    );
  });

  it('validateForm rejects when any required field is empty', () => {
    const requiredTextFields = ['nome', 'assunto', 'mensagem'];

    fc.assert(
      fc.property(
        fc.constantFrom(...requiredTextFields),
        (emptyFieldId) => {
          setupDOM();
          loadModule();

          // Fill all fields with valid data
          setFieldValue('nome', 'João Silva');
          setFieldValue('email', 'joao@example.com');
          setFieldValue('assunto', 'Informação');
          setFieldValue('mensagem', 'Olá, gostaria de saber mais.');
          setCheckbox('consentimento', true);

          // Clear the target field
          setFieldValue(emptyFieldId, '');

          const result = contactForm.validateForm();
          expect(result).toBe(false);
          expect(isErrorVisible(emptyFieldId)).toBe(true);
        }
      ),
      { numRuns: 10 }
    );
  });

  it('validateForm rejects when consent checkbox is unchecked', () => {
    fc.assert(
      fc.property(
        nonEmptyStringArb,
        validEmailArb,
        nonEmptyStringArb,
        nonEmptyStringArb,
        (nome, email, assunto, mensagem) => {
          setupDOM();
          loadModule();

          setFieldValue('nome', nome);
          setFieldValue('email', email);
          setFieldValue('assunto', assunto);
          setFieldValue('mensagem', mensagem);
          setCheckbox('consentimento', false);

          const result = contactForm.validateForm();
          expect(result).toBe(false);
          expect(isErrorVisible('consentimento')).toBe(true);
          expect(getErrorText('consentimento')).toBe(contactForm.MESSAGES.consent);
        }
      ),
      { numRuns: 10 }
    );
  });

  it('validateForm accepts when all fields are valid and consent is checked', () => {
    fc.assert(
      fc.property(
        nonEmptyStringArb,
        validEmailArb,
        nonEmptyStringArb,
        nonEmptyStringArb,
        (nome, email, assunto, mensagem) => {
          setupDOM();
          loadModule();

          setFieldValue('nome', nome);
          setFieldValue('email', email);
          setFieldValue('assunto', assunto);
          setFieldValue('mensagem', mensagem);
          setCheckbox('consentimento', true);

          const result = contactForm.validateForm();
          expect(result).toBe(true);

          // No error messages should be visible
          for (const fieldId of contactForm.REQUIRED_FIELDS) {
            expect(isErrorVisible(fieldId)).toBe(false);
          }
          expect(isErrorVisible('consentimento')).toBe(false);
        }
      ),
      { numRuns: 10 }
    );
  });

  it('error messages are always in pt-PT', () => {
    expect(contactForm.MESSAGES.required).toBe('Este campo é obrigatório.');
    expect(contactForm.MESSAGES.email).toBe('Por favor, introduza um endereço de email válido.');
    expect(contactForm.MESSAGES.consent).toBe('Deve aceitar a política de proteção de dados.');
  });
});
