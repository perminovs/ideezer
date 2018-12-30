def deezer_user(request):
    return {
        'user_picture_url': request.session.get('user_picture_url')
    }
