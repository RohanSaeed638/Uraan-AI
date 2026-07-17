from app.core.supabase import supabase

class AuthService:

    def register(
        self,
        email: str,
        password: str,
        full_name: str
    ):

        response = supabase.auth.sign_up({

            "email": email,

            "password": password,

            "options": {
                "data": {
                    "full_name": full_name
                }
            }

        })

        return response

    def login(
        self,
        email,
        password
    ):

        return supabase.auth.sign_in_with_password({

            "email": email,

            "password": password

        })

    def logout(self):

        return supabase.auth.sign_out()
    
auth_service = AuthService()