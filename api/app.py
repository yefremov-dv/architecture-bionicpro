from flask import Flask, request, jsonify
import jwt
import random
import string
import os

# Публичный ключ Keycloak для проверки подписи токена
KEYCLOAK_PUBLIC_KEY = os.getenv('KEYCLOAK_PUBLIC_KEY')
SECRET_KEY = "oNwoLQdvJAvRcL89SydqCWCe5ry1jMgq"  # Добавляем секретный ключ

app = Flask(__name__)

@app.route('/reports', methods=['GET'])
def generate_report():
    auth_header = request.headers.get('Authorization')
    secret_key = request.args.get('secret')  # Берем секрет из GET-параметра

    # Проверка секретного ключа
    if secret_key != SECRET_KEY:
        return jsonify({"message": "Unauthorized access: Invalid secret key."}), 401

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