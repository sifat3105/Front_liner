from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.throttling import ScopedRateThrottle
from utils.base_view import BaseAPIView as APIView
from utils.permission import IsAdmin, RolePermission, IsOwnerOrParentHierarchy
from .models import SocialPost, SocialMedia, SocialPostPublish
from .serializers import SocialPostSerializer, SocialMediaSerializer, SocialPostPublishSerializer
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page
from django.conf import settings
from apps.social.models import SocialAccount, FacebookPage, FacebookPage

from .utils.publish_Facebook_post import fb_post


app_id = settings.FACEBOOK_APP_ID
app_secret = settings.FACEBOOK_APP_SECRET

class SocialPostView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_post"
    def get(self, request):
        posts = SocialPost.objects.filter(author=request.user)
        serializer = SocialPostSerializer(posts, many=True)
        return self.success(
            message="Social post fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data
        )

    def post(self, request):
        post_data = {
            'title': request.data.get('title'),
            'caption': request.data.get('caption'),
            'scheduled_at': request.data.get('scheduled_at'),
            'is_published': request.data.get('is_published', False),
        }
        serializer = SocialPostSerializer(data=post_data, context={"request": request})
        if serializer.is_valid():
            post = serializer.save()
            media_errors = []
            i = 0
            
            while True:
                file_key = f'media[{i}].file'
                media_type_key = f'media[{i}].media_type'
                
                if file_key in request.FILES:
                    try:
                        SocialMedia.objects.create(
                            post=post,
                            file=request.FILES[file_key],
                            media_type=request.data.get(media_type_key, 'image')
                        )
                    except Exception as e:
                        media_errors.append({f'media_{i}': str(e)})
                else:
                    break
                i += 1
            return self.success(
                message="Social post created successfully",
                status_code=status.HTTP_201_CREATED,
                data=serializer.data
            )
        return self.error(
            message="Invalid data",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
class SocialMediaGalleryView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_post"

    def get(self, request):
        media = SocialMedia.objects.filter(post__author=request.user)
        serializer = SocialMediaSerializer(media, many=True)
        return self.success(
            message="Social media fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data
        )
    

class SocialPostPublishView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "social_post"

    def get(self, request):
        publish = SocialPostPublish.objects.filter(post__author=request.user)
        serializer = SocialPostPublishSerializer(publish, many=True)
        return self.success(
            message="Social post publish fetched successfully",
            status_code=status.HTTP_200_OK,
            data=serializer.data
        )
    
    def post(self, request):
        p_id = request.data.get("post_id")
        pfm = request.data.get("platform")
        
        try:
            post = SocialPost.objects.get(id=p_id)
            if post.is_published:
                return self.error(
                    message="Post is already published",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            publish = SocialPostPublish.objects.get_or_create(
                post=post, 
                platform=pfm,
                status="pending"
            )[0]
            media_urls = []
            for m in post.media.all():
                media_urls.append(f"{request.build_absolute_uri(m.file.url)}")
            
            if pfm == "facebook":
                fb_page_id = request.data.get("fb_page_id")
                page = FacebookPage.objects.get(user=request.user, id=fb_page_id)
                platform_post_id = fb_post(
                    page.page_id,
                    page.page_access_token,
                    post.caption,
                    media_urls
                )
                publish.status = "published"
                publish.platform_post_id = platform_post_id
                publish.save()
                post.is_published = True
                post.save()
            return self.success(
                message="Social post published successfully",
                status_code=status.HTTP_200_OK,
                data={}
            )
        except Exception as e:
            return self.error(
                message="Invalid data",
                errors={"detail": str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
class SocialPlatformListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = []
        platforms = SocialAccount.objects.filter(user=request.user)
        for platform in platforms:
            data.append({
                'id': platform.id,
                'platform': platform.platform,
            })

        return self.success(
            message="Platform list fetched successfully",
            status_code=status.HTTP_200_OK,
            data=data
        )
        
class PlatformPageListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        platform = request.GET.get('platform')
        data = []
        if platform == 'facebook':
            pages = FacebookPage.objects.filter(user=request.user)
            for page in pages:
                data.append({
                    'id': page.id,
                    'name': page.page_name,
                })

        return self.success(
            message="Page list fetched successfully",
            status_code=status.HTTP_200_OK,
            data=data
        )
    

                


 





    



    
