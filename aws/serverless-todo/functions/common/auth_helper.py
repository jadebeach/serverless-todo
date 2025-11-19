def get_user_id_from_event(event):
  """
  Get Cognito User ID from API Gateway event.

  Args:
    event: Lambda event object
  Returns:
    str: Cognito User ID (sub claim)
  Raises:
    ValueError: this returns when the User ID was not found in the request context
  """

  try:
    authorizer = event.get('requestContext', {}).get('authorizer', {})

    claims = authorizer.get('claims', {})
    user_id = claims.get('sub')

    if not user_id:
      raise ValueError('User ID not found in request context')

    return user_id

  except Exception as e:
    print(f"Error extracting user_id: {e}")
    raise ValueError(f"Failed to get user ID: {str{e}}")
