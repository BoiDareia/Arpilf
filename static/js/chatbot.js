/**
 * Chatbot client-side da ARPILF — lógica de correspondência por keywords.
 * Requisitos: 9.2 (mensagem de boas-vindas), 9.3 (respostas baseadas em conteúdo),
 *             9.4 (fallback com contactos), 9.5 (open-source, sem custos)
 *
 * Carrega knowledge-base.json via fetch(), normaliza o input do visitante
 * (lowercase, remover acentos portugueses), tokeniza em palavras, e pesquisa
 * por correspondência de keywords nos patterns da base de conhecimento.
 */
(function () {
  'use strict';

  /**
   * Mapa de acentos portugueses para caracteres ASCII.
   * Usado na normalização de input para correspondência de keywords.
   */
  var ACCENT_MAP = {
    'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a',
    'é': 'e', 'è': 'e', 'ê': 'e',
    'í': 'i', 'ì': 'i', 'î': 'i',
    'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o',
    'ú': 'u', 'ù': 'u', 'û': 'u',
    'ç': 'c'
  };

  /** @type {Object|null} Base de conhecimento carregada */
  var knowledgeBase = null;

  /** @type {boolean} Indica se houve erro ao carregar a base */
  var loadError = false;

  /**
   * Mensagem de erro genérica quando a base de conhecimento não carrega.
   * Conforme design doc: "De momento não consigo ajudar. Contacte-nos pelo telefone [phone_number]"
   */
  var LOAD_ERROR_MESSAGE = {
    resposta: 'De momento não consigo ajudar. Contacte-nos pelo telefone 968 807 673 ou email arpilf@arpilf.pt.',
    link: '/contactos/',
    sugestoes: []
  };

  /**
   * Remove acentos portugueses de uma string.
   * @param {string} str — string com possíveis acentos
   * @returns {string} string sem acentos
   */
  function removeAccents(str) {
    var result = '';
    for (var i = 0; i < str.length; i++) {
      var ch = str[i];
      result += ACCENT_MAP[ch] || ch;
    }
    return result;
  }

  /**
   * Normaliza o input do visitante: lowercase e remoção de acentos.
   * @param {string} input — texto do visitante
   * @returns {string} texto normalizado
   */
  function normalizeInput(input) {
    if (typeof input !== 'string') return '';
    return removeAccents(input.toLowerCase());
  }


  /**
   * Tokeniza o input em palavras individuais.
   * Remove pontuação e divide por espaços.
   * @param {string} input — texto normalizado
   * @returns {string[]} array de tokens (palavras)
   */
  function tokenize(input) {
    if (typeof input !== 'string' || input.trim() === '') return [];
    // Remove pontuação e divide por espaços
    return input
      .replace(/[.,!?;:()""«»\-]/g, ' ')
      .split(/\s+/)
      .filter(function (token) { return token.length > 0; });
  }

  /**
   * Pesquisa a melhor correspondência na base de conhecimento.
   * Para cada entrada (exceto fallback), conta quantos patterns
   * aparecem como substring nos tokens do input. Retorna a entrada
   * com mais correspondências, ou fallback se nenhuma for encontrada.
   *
   * @param {string} userInput — texto original do visitante
   * @returns {{ resposta: string, link?: string, sugestoes?: string[] }}
   */
  function findMatch(userInput) {
    // Se houve erro ao carregar, retornar mensagem de erro
    if (loadError || !knowledgeBase) {
      return LOAD_ERROR_MESSAGE;
    }

    var normalized = normalizeInput(userInput);
    var tokens = tokenize(normalized);

    if (tokens.length === 0 && knowledgeBase.fallback) {
      return buildResponse(knowledgeBase.fallback);
    }

    var bestMatch = null;
    var bestScore = 0;

    var keys = Object.keys(knowledgeBase);
    for (var k = 0; k < keys.length; k++) {
      var key = keys[k];
      if (key === 'fallback') continue;

      var entry = knowledgeBase[key];
      if (!entry || !entry.patterns) continue;

      var score = 0;
      for (var p = 0; p < entry.patterns.length; p++) {
        var pattern = normalizeInput(entry.patterns[p]);
        // Check if the pattern appears in the normalized input string
        if (normalized.indexOf(pattern) !== -1) {
          score++;
        }
      }

      if (score > bestScore) {
        bestScore = score;
        bestMatch = entry;
      }
    }

    if (bestMatch) {
      return buildResponse(bestMatch);
    }

    // Sem correspondência — retornar fallback
    if (knowledgeBase.fallback) {
      return buildResponse(knowledgeBase.fallback);
    }

    return LOAD_ERROR_MESSAGE;
  }

  /**
   * Constrói o objeto de resposta a partir de uma entrada da base de conhecimento.
   * @param {Object} entry — entrada da knowledge-base
   * @returns {{ resposta: string, link?: string, sugestoes?: string[] }}
   */
  function buildResponse(entry) {
    var response = { resposta: entry.resposta };
    if (entry.link) response.link = entry.link;
    if (entry.sugestoes && entry.sugestoes.length > 0) {
      response.sugestoes = entry.sugestoes;
    }
    return response;
  }

  /**
   * Carrega a base de conhecimento via fetch().
   * @param {string} [url] — URL do ficheiro JSON (default: '/js/knowledge-base.json')
   * @returns {Promise<Object>} a base de conhecimento carregada
   */
  function loadKnowledgeBase(url) {
    var jsonUrl = url || '/js/knowledge-base.json';

    return fetch(jsonUrl)
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Falha ao carregar knowledge-base.json: ' + response.status);
        }
        return response.json();
      })
      .then(function (data) {
        knowledgeBase = data;
        loadError = false;
        return data;
      })
      .catch(function (err) {
        loadError = true;
        knowledgeBase = null;
        // Log para debug, sem expor detalhes ao visitante
        if (typeof console !== 'undefined' && console.error) {
          console.error('Chatbot: erro ao carregar base de conhecimento', err);
        }
        throw err;
      });
  }

  /**
   * Define a base de conhecimento diretamente (útil para testes).
   * @param {Object} data — objeto da base de conhecimento
   */
  function setKnowledgeBase(data) {
    knowledgeBase = data;
    loadError = false;
  }

  /**
   * Retorna o estado atual de erro de carregamento.
   * @returns {boolean}
   */
  function hasLoadError() {
    return loadError;
  }

  /**
   * Simula um erro de carregamento (útil para testes).
   */
  function setLoadError(value) {
    loadError = !!value;
    if (loadError) knowledgeBase = null;
  }

  // API pública do chatbot
  var chatbotAPI = {
    normalizeInput: normalizeInput,
    removeAccents: removeAccents,
    tokenize: tokenize,
    findMatch: findMatch,
    loadKnowledgeBase: loadKnowledgeBase,
    setKnowledgeBase: setKnowledgeBase,
    hasLoadError: hasLoadError,
    setLoadError: setLoadError,
    LOAD_ERROR_MESSAGE: LOAD_ERROR_MESSAGE
  };

  // Exportar para testes (Node.js / CommonJS) ou browser (window.chatbot)
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = chatbotAPI;
  } else if (typeof window !== 'undefined') {
    window.chatbot = chatbotAPI;
  }
})();