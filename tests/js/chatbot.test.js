/**
 * Feature: arpilf-website-rebuild, Property 13: Correspondência de keywords no chatbot
 *
 * Para qualquer pergunta do visitante que contenha pelo menos uma keyword definida
 * nos patterns de uma entrada da knowledge-base.json, o chatbot deve retornar a
 * resposta correspondente a essa entrada e, se disponível, o link associado.
 *
 * Feature: arpilf-website-rebuild, Property 14: Resposta de fallback do chatbot
 *
 * Para qualquer pergunta do visitante que não corresponda a nenhum pattern na
 * knowledge-base.json, o chatbot deve retornar a mensagem de fallback com os
 * dados de contacto da ARPILF (telefone e email).
 *
 * **Validates: Requirements 9.3, 9.4**
 */
import { describe, it, expect, beforeAll } from 'vitest';
import * as fc from 'fast-check';
import { readFileSync } from 'fs';
import { resolve } from 'path';

// Load chatbot module
const chatbot = require('../../static/js/chatbot.js');

// Load the real knowledge base
const kbPath = resolve(__dirname, '../../static/js/knowledge-base.json');
const knowledgeBase = JSON.parse(readFileSync(kbPath, 'utf-8'));

// --- Helpers ---

/**
 * Collect all non-fallback entries with their patterns, responses, and links.
 */
function getNonFallbackEntries() {
  const entries = [];
  for (const key of Object.keys(knowledgeBase)) {
    if (key === 'fallback') continue;
    const entry = knowledgeBase[key];
    if (entry && entry.patterns && entry.patterns.length > 0) {
      entries.push({ key, patterns: entry.patterns, resposta: entry.resposta, link: entry.link });
    }
  }
  return entries;
}

/**
 * Collect all normalized patterns from all non-fallback entries.
 */
function getAllPatterns() {
  const patterns = [];
  for (const entry of getNonFallbackEntries()) {
    for (const p of entry.patterns) {
      patterns.push(chatbot.normalizeInput(p));
    }
  }
  return patterns;
}

const nonFallbackEntries = getNonFallbackEntries();
const allPatterns = getAllPatterns();

/**
 * Given a question string, find all non-fallback entries whose patterns match it.
 * Returns the set of entry keys that could legitimately be returned.
 */
function getMatchingEntryKeys(question) {
  const normalized = chatbot.normalizeInput(question);
  const matchingKeys = new Set();
  for (const entry of nonFallbackEntries) {
    for (const p of entry.patterns) {
      const normPattern = chatbot.normalizeInput(p);
      if (normalized.indexOf(normPattern) !== -1) {
        matchingKeys.add(entry.key);
        break;
      }
    }
  }
  return matchingKeys;
}

/**
 * Generator: produces a random question string that contains at least one keyword
 * from a randomly chosen KB entry. Returns { entryKey, pattern, question }.
 * The question is guaranteed to match at least the chosen entry.
 */
const questionWithKeywordArb = fc.record({
  entryIndex: fc.integer({ min: 0, max: nonFallbackEntries.length - 1 }),
  patternIndex: fc.nat(),
  prefix: fc.stringMatching(/^[a-zA-Z ]{0,20}$/),
  suffix: fc.stringMatching(/^[a-zA-Z ]{0,20}$/)
}).map(({ entryIndex, patternIndex, prefix, suffix }) => {
  const entry = nonFallbackEntries[entryIndex];
  const pIdx = patternIndex % entry.patterns.length;
  const pattern = entry.patterns[pIdx];
  const question = (prefix + ' ' + pattern + ' ' + suffix).trim();
  return { entryKey: entry.key, pattern, question, entry };
});

/**
 * Generator: produces random strings guaranteed NOT to contain any KB pattern.
 * Uses only consonant clusters and digits that won't accidentally form Portuguese words.
 */
const noMatchStringArb = fc
  .stringMatching(/^[bcdfghjklmnpqrstvwxyz0-9]{3,25}$/)
  .filter((s) => {
    const normalized = chatbot.normalizeInput(s);
    // Ensure no pattern appears as substring in the generated string
    return allPatterns.every((p) => normalized.indexOf(p) === -1);
  });

// --- Tests ---

describe('Property 13: Correspondência de keywords no chatbot', () => {
  beforeAll(() => {
    chatbot.setKnowledgeBase(knowledgeBase);
  });

  it('returns a matching entry response and link when input contains a KB keyword', () => {
    fc.assert(
      fc.property(questionWithKeywordArb, ({ question, entry }) => {
        chatbot.setKnowledgeBase(knowledgeBase);

        const result = chatbot.findMatch(question);

        // The chatbot uses best-score matching: when multiple entries match,
        // the one with the highest score wins. The result must belong to one
        // of the entries whose patterns match the question.
        const matchingKeys = getMatchingEntryKeys(question);
        expect(matchingKeys.size).toBeGreaterThan(0);

        // The returned response must be from one of the matching entries
        const matchingResponses = nonFallbackEntries
          .filter((e) => matchingKeys.has(e.key))
          .map((e) => e.resposta);
        expect(matchingResponses).toContain(result.resposta);

        // The result must NOT be the fallback response (since we have a keyword match)
        expect(result.resposta).not.toBe(knowledgeBase.fallback.resposta);

        // If the matched entry has a link, it must be present
        const matchedEntry = nonFallbackEntries.find((e) => e.resposta === result.resposta);
        if (matchedEntry && matchedEntry.link) {
          expect(result.link).toBe(matchedEntry.link);
        }
      }),
      { numRuns: 10 }
    );
  });
});

describe('Property 14: Resposta de fallback do chatbot', () => {
  beforeAll(() => {
    chatbot.setKnowledgeBase(knowledgeBase);
  });

  it('returns the fallback response with contact info when no pattern matches', () => {
    fc.assert(
      fc.property(noMatchStringArb, (question) => {
        chatbot.setKnowledgeBase(knowledgeBase);

        const result = chatbot.findMatch(question);
        const fallback = knowledgeBase.fallback;

        // Must return the fallback response
        expect(result.resposta).toBe(fallback.resposta);

        // Fallback response must contain phone and email placeholders
        expect(result.resposta).toContain('[phone_number]');
        expect(result.resposta).toContain('[email]');
      }),
      { numRuns: 10 }
    );
  });
});
