<?php
/**
 * GitHub OAuth provider for Decap CMS
 * Self-contained — no dependencies required.
 */

// ── Configuration (replaced by CI/CD pipeline) ────────────────
$client_id     = 'YOUR_CLIENT_ID';
$client_secret = 'YOUR_CLIENT_SECRET';
$scope         = 'repo,user';
// ───────────────────────────────────────────────────────────────

session_start();

$request_uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$request_uri = rtrim($request_uri, '/');

// Route: /oauth → redirect to GitHub authorization
if (preg_match('#/oauth(/index\.php)?$#', $request_uri)) {
    $state = bin2hex(random_bytes(16));
    $_SESSION['oauth_state'] = $state;

    $auth_url = 'https://github.com/login/oauth/authorize?' . http_build_query([
        'client_id'    => $client_id,
        'redirect_uri' => 'https://' . $_SERVER['HTTP_HOST'] . '/oauth/callback/',
        'scope'        => $scope,
        'state'        => $state,
    ]);

    header('Location: ' . $auth_url);
    exit;
}

// Route: /oauth/callback → exchange code for token, return to CMS
if (preg_match('#/oauth/callback#', $request_uri)) {
    if (!isset($_GET['code'])) {
        http_response_code(400);
        die('Missing code parameter');
    }

    $code = $_GET['code'];

    // Exchange authorization code for access token
    $ch = curl_init('https://github.com/login/oauth/access_token');
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => http_build_query([
            'client_id'     => $client_id,
            'client_secret' => $client_secret,
            'code'          => $code,
        ]),
        CURLOPT_HTTPHEADER     => ['Accept: application/json'],
        CURLOPT_RETURNTRANSFER => true,
    ]);

    $response = curl_exec($ch);
    curl_close($ch);

    $data = json_decode($response, true);

    if (!$data || isset($data['error'])) {
        $err = isset($data['error_description']) ? $data['error_description'] : 'Unknown error';
        http_response_code(400);
        die('OAuth error: ' . htmlspecialchars($err));
    }

    $token = $data['access_token'];

    // Build the message exactly as Decap CMS expects
    $content = json_encode([
        'token' => $token,
        'provider' => 'github'
    ]);

    echo <<<HTML
<!DOCTYPE html>
<html>
<head><title>Autenticação</title></head>
<body>
<p>A autenticar...</p>
<script>
(function() {
  var token = "{$token}";
  var provider = "github";

  // Decap CMS expects this exact message format
  var message = "authorization:" + provider + ":success:" + JSON.stringify({token: token, provider: provider});

  console.log("Sending message to opener:", message);

  // Try sending to opener
  if (window.opener) {
    // Send to any origin since we don't know the exact one
    window.opener.postMessage(message, "*");
    console.log("Message sent to opener");
  } else {
    console.error("No window.opener found");
    document.body.innerHTML = "<p>Erro: janela principal não encontrada. Feche esta janela e tente novamente.</p>";
  }
})();
</script>
</body>
</html>
HTML;
    exit;
}

http_response_code(404);
echo 'Not found';
