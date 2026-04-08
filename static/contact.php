<?php
/**
 * Handler do formulário de contacto — ARPILF
 *
 * Processa submissões do formulário de contacto com:
 * - Validação server-side de todos os campos (filter_var, htmlspecialchars)
 * - Verificação de honeypot (rejeição silenciosa de spam)
 * - Rate limiting via sessão PHP (máx. 3 submissões por 15 minutos)
 * - Sanitização de inputs contra HTML/JS/SQL injection
 * - Envio de email via mail()
 * - Redirect 302 para páginas de sucesso ou erro
 *
 * Requirements: 5.2, 5.3, 5.7, 13.3
 */

// ─── Configuração ────────────────────────────────────────────────────────────

/** Endereço de email destinatário (usar variável de ambiente em produção) */
define('RECIPIENT_EMAIL', 'arpilf@arpilf.pt');

/** Nome exibido no campo "From" */
define('SENDER_NAME', 'Website ARPILF');

/** Máximo de submissões permitidas no período de rate limiting */
define('RATE_LIMIT_MAX', 3);

/** Período de rate limiting em segundos (15 minutos) */
define('RATE_LIMIT_WINDOW', 900);

/** URL de redirect em caso de sucesso */
define('SUCCESS_URL', '/contactos/obrigado/');

/** URL de redirect em caso de erro */
define('ERROR_URL', '/contactos/erro/');


// ─── Funções de Sanitização ──────────────────────────────────────────────────

/**
 * Sanitiza uma string de input removendo tags HTML e escapando caracteres especiais.
 *
 * @param string $input O valor de input a sanitizar.
 * @return string O valor sanitizado, seguro para inclusão em email.
 */
function sanitizeInput(string $input): string
{
    $input = trim($input);
    $input = strip_tags($input);
    $input = htmlspecialchars($input, ENT_QUOTES | ENT_HTML5, 'UTF-8');
    return $input;
}


// ─── Funções de Validação ────────────────────────────────────────────────────

/**
 * Valida todos os campos do formulário de contacto.
 *
 * Verifica campos obrigatórios (nome, email, assunto, mensagem, consentimento),
 * formato de email via filter_var, e sanitiza todos os valores.
 *
 * @param array $data Os dados POST do formulário.
 * @return array ['valid' => bool, 'errors' => [...], 'sanitized' => [...]]
 */
function validateFormData(array $data): array
{
    $errors = [];
    $sanitized = [];

    // Nome — obrigatório
    $nome = isset($data['nome']) ? sanitizeInput($data['nome']) : '';
    if ($nome === '') {
        $errors['nome'] = 'O campo Nome é obrigatório.';
    }
    $sanitized['nome'] = $nome;

    // Email — obrigatório + formato válido
    $email = isset($data['email']) ? trim($data['email']) : '';
    if ($email === '') {
        $errors['email'] = 'O campo Email é obrigatório.';
    } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $errors['email'] = 'Por favor, introduza um endereço de email válido.';
    }
    $sanitized['email'] = filter_var($email, FILTER_SANITIZE_EMAIL);

    // Telefone — opcional, sanitizar se presente
    $telefone = isset($data['telefone']) ? sanitizeInput($data['telefone']) : '';
    $sanitized['telefone'] = $telefone;

    // Assunto — obrigatório
    $assunto = isset($data['assunto']) ? sanitizeInput($data['assunto']) : '';
    if ($assunto === '') {
        $errors['assunto'] = 'O campo Assunto é obrigatório.';
    }
    $sanitized['assunto'] = $assunto;

    // Mensagem — obrigatória
    $mensagem = isset($data['mensagem']) ? sanitizeInput($data['mensagem']) : '';
    if ($mensagem === '') {
        $errors['mensagem'] = 'O campo Mensagem é obrigatório.';
    }
    $sanitized['mensagem'] = $mensagem;

    // Consentimento RGPD — obrigatório (checkbox)
    $consentimento = isset($data['consentimento']);
    if (!$consentimento) {
        $errors['consentimento'] = 'Deve aceitar a política de proteção de dados.';
    }
    $sanitized['consentimento'] = $consentimento;

    return [
        'valid'     => empty($errors),
        'errors'    => $errors,
        'sanitized' => $sanitized,
    ];
}


// ─── Verificação de Honeypot ─────────────────────────────────────────────────

/**
 * Verifica se o campo honeypot foi preenchido (indicador de bot/spam).
 *
 * @param array $data Os dados POST do formulário.
 * @return bool true se o honeypot está preenchido (é spam).
 */
function isHoneypotFilled(array $data): bool
{
    return isset($data['_honeypot']) && $data['_honeypot'] !== '';
}


// ─── Rate Limiting ───────────────────────────────────────────────────────────

/**
 * Verifica e atualiza o rate limiting baseado em sessão PHP.
 *
 * Permite no máximo RATE_LIMIT_MAX submissões dentro de RATE_LIMIT_WINDOW segundos.
 * Limpa automaticamente timestamps expirados.
 *
 * @return bool true se o limite foi excedido (deve bloquear).
 */
function isRateLimited(): bool
{
    if (session_status() === PHP_SESSION_NONE) {
        session_start();
    }

    $now = time();

    // Inicializar array de timestamps se não existir
    if (!isset($_SESSION['contact_submissions'])) {
        $_SESSION['contact_submissions'] = [];
    }

    // Remover timestamps fora da janela de rate limiting
    $_SESSION['contact_submissions'] = array_filter(
        $_SESSION['contact_submissions'],
        function ($timestamp) use ($now) {
            return ($now - $timestamp) < RATE_LIMIT_WINDOW;
        }
    );

    // Verificar se excedeu o limite
    if (count($_SESSION['contact_submissions']) >= RATE_LIMIT_MAX) {
        return true;
    }

    // Registar esta submissão
    $_SESSION['contact_submissions'][] = $now;

    return false;
}


// ─── Envio de Email ──────────────────────────────────────────────────────────

/**
 * Envia o email de contacto via mail().
 *
 * @param array $sanitized Os dados sanitizados do formulário.
 * @return bool true se o email foi enviado com sucesso.
 */
function sendContactEmail(array $sanitized): bool
{
    $to = RECIPIENT_EMAIL;

    $subject = 'Contacto Website ARPILF: ' . $sanitized['assunto'];

    // Construir corpo do email em texto simples
    $body  = "Nova mensagem recebida através do formulário de contacto do website ARPILF.\n\n";
    $body .= "─────────────────────────────────────\n";
    $body .= "Nome: "     . $sanitized['nome']  . "\n";
    $body .= "Email: "    . $sanitized['email'] . "\n";
    if ($sanitized['telefone'] !== '') {
        $body .= "Telefone: " . $sanitized['telefone'] . "\n";
    }
    $body .= "Assunto: "  . $sanitized['assunto']  . "\n";
    $body .= "─────────────────────────────────────\n\n";
    $body .= "Mensagem:\n" . $sanitized['mensagem'] . "\n\n";
    $body .= "─────────────────────────────────────\n";
    $body .= "Consentimento RGPD: Sim\n";
    $body .= "Data/Hora: " . date('Y-m-d H:i:s') . "\n";
    $body .= "IP: " . ($_SERVER['REMOTE_ADDR'] ?? 'desconhecido') . "\n";

    // Cabeçalhos do email
    $headers  = "From: " . SENDER_NAME . " <" . $to . ">\r\n";
    $headers .= "Reply-To: " . $sanitized['email'] . "\r\n";
    $headers .= "Content-Type: text/plain; charset=UTF-8\r\n";
    $headers .= "X-Mailer: ARPILF-Website-Contact-Form\r\n";

    // TODO: Implementar audit logging para registo de submissões
    // auditLog('contact_form_submission', ['email' => $sanitized['email'], 'timestamp' => date('c')]);

    return mail($to, $subject, $body, $headers);
}


// ─── Resposta HTTP ───────────────────────────────────────────────────────────

/**
 * Envia uma resposta ao cliente.
 *
 * Para pedidos AJAX (X-Requested-With: XMLHttpRequest), retorna JSON.
 * Para pedidos normais, faz redirect 302.
 *
 * @param bool   $success  Se a operação foi bem-sucedida.
 * @param array  $errors   Erros de validação (se aplicável).
 * @param string $message  Mensagem adicional (ex: rate limit).
 */
function sendResponse(bool $success, array $errors = [], string $message = ''): void
{
    $isAjax = isset($_SERVER['HTTP_X_REQUESTED_WITH'])
        && strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) === 'xmlhttprequest';

    if ($isAjax) {
        header('Content-Type: application/json; charset=UTF-8');
        if ($success) {
            http_response_code(200);
            echo json_encode(['success' => true]);
        } else {
            http_response_code(400);
            $response = ['success' => false, 'errors' => $errors];
            if ($message !== '') {
                $response['message'] = $message;
            }
            echo json_encode($response);
        }
    } else {
        if ($success) {
            header('Location: ' . SUCCESS_URL, true, 302);
        } else {
            header('Location: ' . ERROR_URL, true, 302);
        }
    }
    exit;
}


// ─── Processamento Principal ─────────────────────────────────────────────────

// Não executar o fluxo principal quando incluído em testes
if (php_sapi_name() !== 'cli' && !defined('TESTING')) {

    // Aceitar apenas pedidos POST
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        header('Location: /contactos/', true, 302);
        exit;
    }

    // 1. Verificar honeypot — rejeitar silenciosamente (simular sucesso)
    if (isHoneypotFilled($_POST)) {
        // TODO: Audit log — spam detectado via honeypot
        // auditLog('honeypot_triggered', ['ip' => $_SERVER['REMOTE_ADDR'] ?? '', 'timestamp' => date('c')]);
        sendResponse(true);
    }

    // 2. Verificar rate limiting
    if (isRateLimited()) {
        // TODO: Audit log — rate limit excedido
        // auditLog('rate_limit_exceeded', ['ip' => $_SERVER['REMOTE_ADDR'] ?? '', 'timestamp' => date('c')]);
        sendResponse(false, [], 'Demasiadas tentativas. Por favor, aguarde alguns minutos.');
    }

    // 3. Validar e sanitizar dados do formulário
    $result = validateFormData($_POST);

    if (!$result['valid']) {
        sendResponse(false, $result['errors']);
    }

    // 4. Enviar email
    $emailSent = sendContactEmail($result['sanitized']);

    if ($emailSent) {
        // TODO: Audit log — email enviado com sucesso
        // auditLog('contact_email_sent', ['email' => $result['sanitized']['email'], 'timestamp' => date('c')]);
        sendResponse(true);
    } else {
        // TODO: Audit log — falha no envio de email
        // auditLog('contact_email_failed', ['email' => $result['sanitized']['email'], 'timestamp' => date('c')]);
        sendResponse(false, [], 'Não foi possível enviar a mensagem. Por favor, contacte-nos por telefone ou email.');
    }

} // end of main execution guard
