<?php
/**
 * GitHub OAuth provider for Decap CMS
 * Self-contained — no dependencies required.
 *
 * Setup:
 * 1. Create a GitHub OAuth App (Settings > Developer settings > OAuth Apps)
 *    - Callback URL: https://arpilf.pt/oauth/callback/
 * 2. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET below
 * 3. Upload this file to public_html/oauth/index.php on cPanel
 */

// ── Configuration ──────────────────────────────────────────────
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
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($http_code !== 200) {
        http_response_code(500);
        die('Failed to get access token');
    }

    $data = json_decode($response, true);

    if (isset($data['error'])) {
        http_response_code(400);
        die('OAuth error: ' . htmlspecialchars($data['error_description']));
    }

    $token    = $data['access_token'];
    $provider = 'github';

    // Return the token to Decap CMS via postMessage
    $json_message = json_encode(['token' => $token, 'provider' => $provider]);
    ?>
    <!DOCTYPE html>
    <html>
    <head><title>Autenticação</title></head>
    <body>
      <script>
        (function() {
          function receiveMessage(e) {
            console.log("receiveMessage", e);
            window.opener.postMessage(
              "authorization:github:success:<?php echo $json_message; ?>",
              e.origin
            );
            window.removeEventListener("message", receiveMessage, false);
          }
          window.addEventListener("message", receiveMessage, false);
          window.opener.postMessage("authorizing:github", "*");
        })();
      </script>
    </body>
    </html>
    <?php
    exit;
}

http_response_code(404);
echo 'Not found';
