from ..models import PostMediaFile

def save_media_files(request, post):
    i = 0
    while True:
        file_key = f"media[{i}].file"
        type_key = f"media[{i}].media_type"

        if file_key not in request.FILES:
            break

        PostMediaFile.objects.create(
            post=post,
            file=request.FILES[file_key],
            media_type=request.data.get(type_key, "image")
        )
        i += 1
