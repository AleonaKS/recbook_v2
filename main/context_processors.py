def add_user_id(request):
    return {'user_id': getattr(request.user, 'id', None)}
