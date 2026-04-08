/**
 * Validação client-side do formulário de contacto.
 * Requisitos: 5.3 (mensagens de erro em pt-PT), 5.6 (validação client-side)
 *
 * Valida: campos obrigatórios vazios, formato de email (regex),
 * checkbox de consentimento RGPD.
 * Mostra mensagens de erro em pt-PT junto a cada campo inválido.
 * Impede submissão se a validação falhar.
 */
(function () {
  'use strict';

  // Regex para validação de email — aceita formatos padrão
  var EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  // Mensagens de erro em pt-PT
  var MESSAGES = {
    required: 'Este campo é obrigatório.',
    email:    'Por favor, introduza um endereço de email válido.',
    consent:  'Deve aceitar a política de proteção de dados.'
  };

  // Campos obrigatórios (excluindo consentimento, tratado à parte)
  var REQUIRED_FIELDS = ['nome', 'email', 'assunto', 'mensagem'];

  /**
   * Mostra uma mensagem de erro junto ao campo.
   * @param {string} fieldId — id do campo
   * @param {string} message — texto do erro em pt-PT
   */
  function showError(fieldId, message) {
    var errorEl = document.getElementById(fieldId + '-error');
    if (!errorEl) return;
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
  }

  /**
   * Esconde a mensagem de erro de um campo.
   * @param {string} fieldId — id do campo
   */
  function hideError(fieldId) {
    var errorEl = document.getElementById(fieldId + '-error');
    if (!errorEl) return;
    errorEl.textContent = '';
    errorEl.classList.add('hidden');
  }

  /**
   * Valida que um campo de texto não está vazio.
   * @param {string} fieldId — id do campo
   * @returns {boolean} true se válido
   */
  function validateRequired(fieldId) {
    var field = document.getElementById(fieldId);
    if (!field) return true;
    var value = field.value.trim();
    if (value === '') {
      showError(fieldId, MESSAGES.required);
      return false;
    }
    hideError(fieldId);
    return true;
  }

  /**
   * Valida o formato do email.
   * Verifica primeiro se está vazio (campo obrigatório), depois o formato.
   * @returns {boolean} true se válido
   */
  function validateEmail() {
    var field = document.getElementById('email');
    if (!field) return true;
    var value = field.value.trim();
    if (value === '') {
      showError('email', MESSAGES.required);
      return false;
    }
    if (!EMAIL_REGEX.test(value)) {
      showError('email', MESSAGES.email);
      return false;
    }
    hideError('email');
    return true;
  }

  /**
   * Valida que a checkbox de consentimento RGPD está marcada.
   * @returns {boolean} true se marcada
   */
  function validateConsent() {
    var checkbox = document.getElementById('consentimento');
    if (!checkbox) return true;
    if (!checkbox.checked) {
      showError('consentimento', MESSAGES.consent);
      return false;
    }
    hideError('consentimento');
    return true;
  }

  /**
   * Valida todo o formulário de contacto.
   * @returns {boolean} true se todos os campos são válidos
   */
  function validateForm() {
    var isValid = true;

    // Validar campos obrigatórios de texto (exceto email, tratado à parte)
    for (var i = 0; i < REQUIRED_FIELDS.length; i++) {
      var fieldId = REQUIRED_FIELDS[i];
      if (fieldId === 'email') {
        // Email tem validação própria (formato + obrigatório)
        if (!validateEmail()) isValid = false;
      } else {
        if (!validateRequired(fieldId)) isValid = false;
      }
    }

    // Validar consentimento RGPD
    if (!validateConsent()) isValid = false;

    return isValid;
  }

  // Ligar ao evento submit do formulário
  var form = document.getElementById('contact-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      if (!validateForm()) {
        e.preventDefault();
      }
    });
  }

  // Exportar funções para testes
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      validateRequired: validateRequired,
      validateEmail: validateEmail,
      validateConsent: validateConsent,
      validateForm: validateForm,
      showError: showError,
      hideError: hideError,
      EMAIL_REGEX: EMAIL_REGEX,
      MESSAGES: MESSAGES,
      REQUIRED_FIELDS: REQUIRED_FIELDS
    };
  } else if (typeof window !== 'undefined') {
    window.contactFormValidation = {
      validateRequired: validateRequired,
      validateEmail: validateEmail,
      validateConsent: validateConsent,
      validateForm: validateForm,
      showError: showError,
      hideError: hideError,
      EMAIL_REGEX: EMAIL_REGEX,
      MESSAGES: MESSAGES,
      REQUIRED_FIELDS: REQUIRED_FIELDS
    };
  }
})();
