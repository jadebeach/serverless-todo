def get_user_id_from_event(event):
    """
    API Gateway eventからCognitoユーザーIDを取得
    
    Args:
        event: Lambda event object
        
    Returns:
        str: Cognito User ID (sub claim)
        
    Raises:
        ValueError: 認証情報が見つからない場合
    """
    try:
        # API Gatewayの認証情報から取得
        authorizer = event.get('requestContext', {}).get('authorizer', {})
        
        # Cognitoの場合、claimsにsubが含まれる
        claims = authorizer.get('claims', {})
        user_id = claims.get('sub')
        
        if not user_id:
            raise ValueError('User ID not found in request context')
        
        return user_id
        
    except Exception as e:
        print(f"Error extracting user_id: {e}")
        raise ValueError(f'Failed to get user ID: {str(e)}')