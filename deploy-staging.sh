#!/bin/bash
# Deploy ARPILF website to staging (arpilf.pt/novo/)
#
# Usage:
#   ./deploy-staging.sh
#
# Prerequisites:
#   - Hugo installed
#   - Tailwind CSS CLI (tailwindcss or tailwindcss.exe) in project root
#   - lftp installed (or use FileZilla manually)
#
# After running, upload the contents of public/ to public_html/novo/ on cPanel.

set -e

echo "=== ARPILF Staging Build ==="

# 1. Compile Tailwind CSS (minified)
echo "[1/3] Compiling Tailwind CSS..."
if [ -f "./tailwindcss.exe" ]; then
    ./tailwindcss.exe -i assets/css/main.css -o static/css/style.css --minify
elif [ -f "./tailwindcss" ]; then
    ./tailwindcss -i assets/css/main.css -o static/css/style.css --minify
else
    echo "ERROR: Tailwind CSS CLI not found. Download it first."
    exit 1
fi

# 2. Build Hugo with staging config (baseURL = /novo/)
echo "[2/3] Building Hugo (staging)..."
hugo --minify --environment staging --cleanDestinationDir

# 3. Add a noindex robots.txt to prevent search engine indexing
echo "[3/3] Adding noindex robots.txt..."
cat > public/robots.txt << 'EOF'
User-agent: *
Disallow: /
EOF

echo ""
echo "=== Build complete! ==="
echo ""
echo "Output is in: public/"
echo ""
echo "Next steps:"
echo "  1. Connect to cPanel via SFTP (FileZilla or lftp)"
echo "  2. Upload the contents of public/ to public_html/novo/"
echo "  3. Test at: https://arpilf.pt/novo/"
echo ""
echo "To deploy with lftp:"
echo "  lftp -e \"mirror --reverse --delete --verbose public/ /public_html/novo/; bye\" \\"
echo "    -u USERNAME,PASSWORD sftp://ftp.arpilf.pt"
