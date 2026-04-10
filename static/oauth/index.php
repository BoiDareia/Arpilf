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
        $errContent = json_encode($err);
        echo <<<HTML
<!DOCTYPE html>
<html><head><title>Erro</title></head>
<body>
<script>
(function() {
  function receiveMessage(e) {
    window.opener.postMessage(
      'authorization:github:error:{$errContent}',
      e.origin
    );
  }
  window.addEventListener("message", receiveMessage, false);
  window.opener.postMessage("authorizing:github", "*");
})();
</script>
</body>
</html>
HTML;
        exit;
    }

    $token = $data['access_token'];
    $content = json_encode(['token' => $token, 'provider' => 'github']);

    echo <<<HTML
<!DOCTYPE html>
<html><head><title>Autenticação</title></head>
<body>
<script>
(function() {
  function receiveMessage(e) {
    console.log("receiveMessage %o", e);
    // Send token to main window
    window.opener.postMessage(
      'authorization:github:success:{$content}',
      e.origin
    );
  }
  window.addEventListener("message", receiveMessage, false);
  // Start handshake with parent
  console.log("Sending message: github");
  window.opener.postMessage("authorizing:github", "*");
})();
</script>
</body>
</html>
HTML;
    exit;
}

http_response_code(404);
echo 'Not found';
