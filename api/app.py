from flask import Flask, request, jsonify
import jwt
import random
import string

# Публичный ключ Keycloak для проверки подписи токена
KEYCLOAK_PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApQup5lU7M+RRgfpuMM/4VNAwxX/Cc/J/nbsePfir3kF5OZ+VbGbn4txaPSntc+rlqZzgQQqRylIdHveABfpd+k4/XtjWawheNoAtv7244ymf8uB6g3hT0bcxQNt8r7RsDuzwOuh56mjYuTA2+6ApAw5H6/3vkYHrM1b6ZeNy30wzfqpI3yiKl2RPCjbTw0u6sf6GHVibu58qRjFPBSswoCBR86UtnwRg3nOevwu4MO61BOv3j6Bs5G+ngXiwcwzgrDevI3pbwKXF1sw4sXmDtI4gNkJpyQvb+cHl1+7oYcLh4xgjFt+KRV8I00v8j9VQuHwPX0vfyC/9uv84JC8IVwIDAQAB
-----END PUBLIC KEY-----
"""

app = Flask(__name__)

@app.route('/reports', methods=['GET'])
def generate_report():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer"):
        return jsonify({"message": "Missing Authorization header"}), 401

    token = auth_header.split()[1]
    try:
        # Декодируем токен и проверяем его подпись и срок действия
        decoded_token = jwt.decode(
            token,
            KEYCLOAK_PUBLIC_KEY,
            algorithms=["RS256"],
            verify_exp=True,  # Проверяем срок действия токена
            options={
                "require": ["exp"]  # Требуем обязательного наличия exp (expiration time)
            },
        )
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired"}), 401
    except jwt.InvalidTokenError as e:
        return jsonify({"message": f"Invalid token: {str(e)}"}), 401

    # Получаем информацию о ролях пользователя
    resource_access = decoded_token.get('resource_access', {})
    client_roles = resource_access.get('reports-frontend', {}).get('roles', [])

    if 'prothetic_user' not in client_roles:
        return jsonify({"message": "Access denied: required role is missing"}), 403

    # Генерируем данные отчета
    report_data = []
    for _ in range(random.randint(5, 10)):
        data_point = {
            'title': ''.join(random.choice(string.ascii_letters) for i in range(10)),
            'value': round(random.uniform(1, 100), 2),
        }
        report_data.append(data_point)

    return jsonify(report_data)

if __name__ == '__main__':
    app.run(debug=True)