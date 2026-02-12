from django.contrib.auth.tokens import PasswordResetTokenGenerator

def password_reset_token(user):
    if user is None:
        return 
    
    default_token_generator = PasswordResetTokenGenerator()
    try:
        token = default_token_generator.make_token(user=user)
    except Exception as e:
        raise Exception(f"Error creating password reset token: {str(e)}")
    return token