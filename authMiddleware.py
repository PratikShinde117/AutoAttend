import jwt
from functools import wraps
from flask import request, jsonify
import dotenv
import os
dotenv.load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET")   
def verify_internal_request():
    headers = request.headers

    key = headers.get("x-internal-key") or headers.get("X-Internal-Key")

    expected = os.getenv("INTERNAL_API_KEY")

    print("HEADERS:", dict(headers))
    print("RECEIVED KEY:", repr(key))
    print("EXPECTED KEY:", repr(expected))

    return key and expected and key.strip() == expected.strip()   




def token_required(roles=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):

            
            if not verify_internal_request():
                return jsonify({"error": "Forbidden (internal only)"}), 403

            auth_header = request.headers.get("Authorization")

            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "No token provided"}), 401

            try:
                token = auth_header.split(" ")[1]
                decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

                request.user = decoded

                if roles and decoded.get("role") not in roles:
                    return jsonify({"error": "Access denied"}), 403

                return f(*args, **kwargs)

            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except Exception:
                return jsonify({"error": "Invalid token"}), 401
            

        return wrapper
    return decorator



# def token_required(roles=None):
#     def decorator(f):
#         @wraps(f)
#         def wrapper(*args, **kwargs):
#             auth_header = request.headers.get("Authorization")
#             print("Auth Header:", auth_header)
#             print("SECRET_KEY:", SECRET_KEY)

#             if not auth_header or not auth_header.startswith("Bearer "):
#                 return jsonify({"error": "No token provided"}), 401

#             try:
#                 token = auth_header.split(" ")[1]
#                 decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

#                 # attach user (like req.user in Node)
#                 request.user = decoded

#                 # role check
#                 if roles and decoded.get("role") not in roles:
#                     return jsonify({"error": "Access denied"}), 403

#                 return f(*args, **kwargs)

#             except jwt.ExpiredSignatureError:
#                 return jsonify({"error": "Token expired"}), 401
#             except Exception:
#                 return jsonify({"error": "Invalid token"}), 401

#         return wrapper
#     return decorator
