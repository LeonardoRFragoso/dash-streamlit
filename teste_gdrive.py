import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials

# Carregar o arquivo JSON de credenciais
credentials_json = {
    "type": "service_account",
    "project_id": "multas-444618",
    "private_key_id": "49e323b67671dd175aec33cb42f1dafd00a9064d",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC+e9n/FeZY4vCi
XPxyVJo4/YlS7ux0vm869kKoxBKVVBWUlkGLGhZbVRptMvKL2HitUHL4EXDyu/UM
Bz5NXX6IJXmJ1EjBZBClx/GxIab/OnyB7rcBwmUbPEQf4+GlZ9CqGCuuYiHqiA4o
x98wqF6EETSU29yNnqw1LidtUnx2K831jGmTOLxcFscZAcxtC5RQw0Ngri04yPSk
iwXiuDZcHsOFNkBlJKL6JD10YWtsFhpnV+PDbrEonNfzdBfb3f4Z80p5QOT/abY1
dRyIoVJiIqrNeAWLbmrddDueqbm+AZK13NPcexa1K+vFKELx9hPeQVu2IikdeaYn
HsuCQoExAgMBAAECggEAAbVTJGxCG1h3r4EVe4ICOxIdBesiID7n+Pel6+UMRJ4T
Lni1gEWc3zdRbBrJnZL0rBs9WLexU1/3p+K1vpRg0uBBKYkHmQJoetAi/QNv/7h6
zuCA8ClZ5kdhVgbham4WqzvZwm/bXYLYW6nFOOa9qEIOPmqFXRjH8xcln9+eQaIJ
dW5e3NLGq0Xf/CQpVaPCS44uT1n7lAAlQnK0lAjVYYx3FIUy0P4f8DZmYBcZxXS7
McrCw9ilBoIUPZUmFL97Ev31trMmkHLnu2Uv/SYhK3yt/BJK5rGL+VhlkhwZFtm6
LPVisfZ9TWocrdc5lqYO8b69Xw4u4kMDVKAyV91ZZQKBgQDzB8fkhxmL9CXAFwGs
vnnw0LnlA/5JdRS4Q0wSXG3SsU/2VuW30Nves/6z//Txgva9ANnlhZdg7x94N5+M
+rg9iNa4PB+5wfXF7JUwG2uzUzTcFDB+vmkv6GZhX6pabzJzXAL2zOz4hLrvqa+n
osMkDeXLCYTNcYu+L/KvZGfdVQKBgQDIpjFIF+4xJZvDYVL/3SIOE0Qebfthihzf
5EFxu3edif11h+sei9EElwNqiMvsjAVGTjqsou4gkrvglr882bdOdk9VTMKJmq0G
6WnUG0XQ4QsAmEYfeG+K7ex1vOjas9RyWl5spMM/4MVxSxkIQRaVvRznHPccGps3
8GjGZMQ0bQKBgG43xyYTRzi7nytAw9euAut+HfCJIRf7a0wt6SAinwQAuj0EJ+Z3
aF/VzdugZ1vogzIwYqG/NmoVyHXi9A8h3dC6cHbZfaHnHymGJBrPNMb9I2n0FhJF
FLtPcK8UjdO5vm2m+wkm4wnKWGU81Zb3L/z3+JFeXcY2iqPUZwG4TYqJAoGBALQV
lT2jXMD3hCmDfD7wddQ0LnsxMuGEWA4Ki0JMgzr90mJeLwQncN2xu/st8/jGYyWK
qNaxFRBfIgicw98VeJQPU3y3fBKMpKcDb1xTbgHfOUS7ZpRwP4xtpkC14DgKFq7b
tMvFxQfb8NmSEVF7OY4DQaGcOZ0btBwsxZzqa76xAoGBAMTKbRBTDpkj4oMrFfP1
XTmbwFFonwSsLU/1zC1biEf6hIKDQX9t6kRUKbYfc+QJ+bIctznwYuR3QVf0cUu6
LZfHf4rJ4YFz7etwzzpFSiyAjbFgsB/UjcKPYPjLV+G1REpMsNH8Vt7+2ntdfsHw
Ul7EX5wQZR1VxLg9aEpfECWG
-----END PRIVATE KEY-----""",
    "client_email": "driveapiaccess@multas-444618.iam.gserviceaccount.com",
    "client_id": "107610768041934442306",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/driveapiaccess%40multas-444618.iam.gserviceaccount.com",
}

# Criar credenciais
credentials = Credentials.from_service_account_info(credentials_json, scopes=["https://www.googleapis.com/auth/drive"])

try:
    # Conectar ao Google Drive API
    service = build("drive", "v3", credentials=credentials)
    
    # Listar os arquivos na pasta principal
    results = service.files().list(pageSize=10, fields="files(id, name)").execute()
    items = results.get('files', [])
    
    if not items:
        print("Nenhum arquivo encontrado.")
    else:
        print("Arquivos:")
        for item in items:
            print(f"{item['name']} ({item['id']})")

except HttpError as error:
    print(f"Um erro ocorreu: {error}")
